// Dump functions, decompiled C, strings, and pointer tables for a PE.
// Usage: -postScript DumpAll.java <outDir>
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import ghidra.program.model.address.*;
import ghidra.program.model.data.*;
import ghidra.program.model.mem.*;
import java.io.*;
import java.util.*;

public class DumpAll extends GhidraScript {
    public void run() throws Exception {
        String outDir = getScriptArgs()[0];
        File decompDir = new File(outDir, "decomp");
        decompDir.mkdirs();

        DecompInterface di = new DecompInterface();
        di.setSimplificationStyle("decompile");
        if (!di.openProgram(currentProgram)) {
            println("ERROR: decompiler open failed");
            return;
        }

        PrintWriter fn = new PrintWriter(new FileWriter(new File(outDir, "functions.tsv")));
        fn.println("entry\tname\tsize\tis_thunk\tis_external\tcalling_conv\tparams");
        int count = 0;
        for (Function f : currentProgram.getFunctionManager().getFunctions(true)) {
            int size = (int) f.getBody().getNumAddresses();
            fn.println(f.getEntryPoint() + "\t" + f.getName() + "\t" + size + "\t" + f.isThunk()
                    + "\t" + f.isExternal() + "\t" + f.getCallingConventionName() + "\t" + f.getParameterCount());
            if (f.isExternal() || f.isThunk()) continue;
            DecompileResults r = di.decompileFunction(f, 90, monitor);
            File out = new File(decompDir, String.format("%08x.c", f.getEntryPoint().getOffset()));
            PrintWriter w = new PrintWriter(new FileWriter(out));
            w.println("// " + f.getName() + " @ " + f.getEntryPoint() + " size " + size);
            if (r != null && r.decompileCompleted()) {
                w.println(r.getDecompiledFunction().getC());
            } else {
                w.println("// DECOMPILE FAILED: " + (r == null ? "null" : r.getErrorMessage()));
            }
            w.close();
            count++;
        }
        fn.close();
        println("decompiled " + count + " functions");

        // strings and their references
        PrintWriter sw = new PrintWriter(new FileWriter(new File(outDir, "strings_xrefs.tsv")));
        sw.println("address\tstring\treferenced_from");
        DataIterator it = currentProgram.getListing().getDefinedData(true);
        Memory mem = currentProgram.getMemory();
        while (it.hasNext() && !monitor.isCancelled()) {
            Data d = it.next();
            if (d == null || d.getValue() == null) continue;
            if (d.getDataType() instanceof StringDataType || d.getDataType() instanceof UnicodeDataType) {
                String s = d.getValue().toString().replace("\n", "\\n").replace("\r", "");
                StringBuilder refs = new StringBuilder();
                ReferenceIterator ri = currentProgram.getReferenceManager().getReferencesTo(d.getAddress());
                while (ri.hasNext()) {
                    Reference ref = ri.next();
                    if (refs.length() > 0 && refs.length() < 400) refs.append(",");
                    if (refs.length() < 400) refs.append(ref.getFromAddress());
                }
                sw.println(d.getAddress() + "\t" + s + "\t" + refs);
            }
        }
        sw.close();

        // scan .rdata for arrays of code pointers (candidate vtables)
        PrintWriter vw = new PrintWriter(new FileWriter(new File(outDir, "vtable_candidates.tsv")));
        for (MemoryBlock block : mem.getBlocks()) {
            if (!block.isInitialized()) continue;
            Address start = block.getStart();
            long len = block.getSize();
            long seqStart = -1; int seqCount = 0;
            for (long off = 0; off < len - 8; off += 8) {
                Address a = start.add(off);
                long v;
                try { v = mem.getLong(a); } catch (Exception e) { seqCount = 0; seqStart = -1; continue; }
                Address target = toAddr(v);
                boolean isFunc = target != null && currentProgram.getFunctionManager().getFunctionAt(target) != null;
                if (isFunc) {
                    if (seqCount == 0) seqStart = off;
                    seqCount++;
                } else {
                    if (seqCount >= 3) vw.println(start.add(seqStart) + "\t" + seqCount);
                    seqCount = 0; seqStart = -1;
                }
            }
            if (seqCount >= 3) vw.println(start.add(seqStart) + "\t" + seqCount);
        }
        vw.close();
        println("done");
    }
}
