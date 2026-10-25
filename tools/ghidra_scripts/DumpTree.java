// Dump a call-graph slice: decompile functions reachable from given entry RVAs.
// Usage: -postScript DumpTree.java <outDir> <maxDepth> <maxFuncs> <rva1,rva2,...>
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import java.io.*;
import java.util.*;

public class DumpTree extends GhidraScript {
    public void run() throws Exception {
        String outDir = getScriptArgs()[0];
        int maxDepth = Integer.parseInt(getScriptArgs()[1]);
        int maxFuncs = Integer.parseInt(getScriptArgs()[2]);
        String[] roots = getScriptArgs()[3].split(",");

        new File(outDir).mkdirs();
        DecompInterface di = new DecompInterface();
        di.setSimplificationStyle("decompile");
        di.openProgram(currentProgram);

        Set<Long> seen = new HashSet<>();
        PrintWriter edges = new PrintWriter(new FileWriter(new File(outDir, "callgraph.tsv")));
        PrintWriter idx = new PrintWriter(new FileWriter(new File(outDir, "index.tsv")));

        // BFS
        ArrayDeque<Object[]> q = new ArrayDeque<>();
        for (String r : roots) {
            long v = Long.parseLong(r.trim(), 16);
            q.add(new Object[]{v, 0});
        }
        int started = 0;
        while (!q.isEmpty() && started < maxFuncs) {
            Object[] item = q.poll();
            long va = (Long) item[0];
            int depth = (Integer) item[1];
            if (seen.contains(va)) continue;
            seen.add(va);
            Address a = currentProgram.getImageBase().add(va);
            Function f = getFunctionAt(a);
            if (f == null) { try { disassemble(a); } catch (Exception e) {} f = getFunctionAt(a); }
            if (f == null) { try { f = createFunction(a, null); } catch (Exception e) {} }
            if (f == null) { continue; }
            started++;
            idx.println(String.format("%x\t%s\t%d", va, f.getName(), f.getBody().getNumAddresses()));
            DecompileResults res = di.decompileFunction(f, 60, monitor);
            PrintWriter w = new PrintWriter(new FileWriter(new File(outDir, String.format("%x.c", va))));
            w.println("// " + f.getName() + " @ " + a + " size " + f.getBody().getNumAddresses() + " depth " + depth);
            if (res != null && res.decompileCompleted()) {
                w.println(res.getDecompiledFunction().getC());
                for (Function callee : res.getDecompiledFunction() != null ? f.getCalledFunctions(monitor) : Collections.<Function>emptySet()) {
                    edges.println(String.format("%x\t%x\t%s", va, callee.getEntryPoint().getOffset(), callee.getName()));
                    if (depth + 1 <= maxDepth) q.add(new Object[]{callee.getEntryPoint().getOffset(), depth + 1});
                }
            } else {
                w.println("// FAILED " + (res == null ? "" : res.getErrorMessage()));
            }
            w.close();
        }
        edges.close(); idx.close();
        println("dumped " + started + " functions");
    }
}
