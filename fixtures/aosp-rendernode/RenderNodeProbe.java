package org.archtv.aospprobe;

import android.graphics.RenderNode;

public final class RenderNodeProbe {
    private static void require(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }
    public static void main(String[] args) {
        System.load(args[0]);
        System.load(args[1]);
        RenderNode[] nodes = new RenderNode[64];
        long previous = 0;
        for (int i = 0; i < nodes.length; ++i) {
            RenderNode node = new RenderNode(i == 0 ? null : "linux-node-"+i);
            nodes[i] = node;
            long id = node.getUniqueId();
            require(id > previous, "unique native object ID");
            previous = id;
            require(!node.hasDisplayList(), "new object has no recording");
            int left = i-20, top = 3*i-5;
            require(node.setPosition(left,top,left+64+i,top+48+i), "new bounds change");
            require(!node.setPosition(left,top,left+64+i,top+48+i), "bounds idempotence");
            require(node.getLeft()==left && node.getTop()==top && node.getRight()==left+64+i
                    && node.getBottom()==top+48+i && node.getWidth()==64+i && node.getHeight()==48+i,
                    "native integer properties");
            boolean initial = node.getClipToBounds();
            require(node.setClipToBounds(!initial) && node.getClipToBounds()!=initial, "native clip update");
            require(!node.setClipToBounds(!initial), "clip idempotence");
            node.setClipToBounds(initial);
            require(node.getAlpha()==1f, "native alpha default");
            float alpha = .25f + (i%3)*.125f;
            require(node.setAlpha(alpha) && node.getAlpha()==alpha, "native float properties");
            require(!node.setAlpha(alpha), "alpha idempotence");
            node.discardDisplayList();
            require(!node.hasDisplayList(), "empty display list remains empty");
        }
        for (int i = 0; i < nodes.length; ++i) {
            require(nodes[i].getWidth()==64+i && nodes[i].getHeight()==48+i
                    && nodes[i].getAlpha()==.25f+(i%3)*.125f, "independent native objects");
        }
        try { nodes[0].setElevation(2f); throw new AssertionError("unregistered method accepted"); }
        catch (UnsatisfiedLinkError expected) {
            require(expected.getMessage().contains("nSetElevation"), "explicit unsupported boundary");
        }
        System.out.println("AOSP_RENDERNODE_PROPERTIES_OK objects=64 registered_methods=16 unsupported_rejected=1");
    }
}
