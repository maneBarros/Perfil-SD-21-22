import spullara.nio.channels.FutureSocketChannel;

import java.nio.ByteBuffer;
import java.util.ArrayDeque;
import java.util.Queue;
import java.util.concurrent.CompletableFuture;

public class LineBuffer {
    private FutureSocketChannel socketChannel;
    private ByteBuffer buf;
    private String currentLine;
    private Queue<String> lines;

    public LineBuffer(FutureSocketChannel socketChannel) {
        this.socketChannel = socketChannel;
        this.buf = ByteBuffer.allocate(100);
        this.currentLine = "";
        this.lines = new ArrayDeque<>();
    }

    public CompletableFuture<String> readLine() {
        if (!this.lines.isEmpty()) return CompletableFuture.completedFuture(lines.poll());

        return this.socketChannel
                .read(this.buf)
                .thenApply(this::extractLines)
                .thenCompose(n -> n > 0 ? CompletableFuture.completedFuture(lines.poll()) : readLine());
    }

    public CompletableFuture<Void> writeLine(String line) {
        return this.socketChannel
                .write(ByteBuffer.wrap(line.getBytes()))
                .thenAccept(n -> {/* do something with nr of bytes written*/});
    }

    public void close() {
        this.socketChannel.close();
    }

    private int extractLines(int bytesRead) {
        byte[] bytes = new byte[bytesRead];
        this.buf.flip();
        this.buf.get(bytes);
        this.buf.flip();
        for (byte b : bytes) {
            char c = (char) b;
            this.currentLine = this.currentLine + c;

            if (c == '\n') {
                this.lines.add(currentLine);
                currentLine = "";
            }
        }

        return this.lines.size();

    }
}
