import java.nio.ByteBuffer;
import java.nio.channels.SelectionKey;
import java.util.ArrayDeque;
import java.util.List;
import java.util.Queue;

public class ChatSession {
    private final Queue<ByteBuffer> pendingMessages = new ArrayDeque<>();
    private final SelectionKey myKey;

    public ChatSession(SelectionKey key) {
        this.myKey = key;
    }

    public ByteBuffer getMessage() {
        ByteBuffer buf = pendingMessages.poll();
        if (this.pendingMessages.isEmpty()) this.myKey.interestOps(SelectionKey.OP_READ);

        return buf;
    }

    public void addMessage(ByteBuffer buf) {
        pendingMessages.add(buf);
        this.myKey.interestOps(SelectionKey.OP_READ | SelectionKey.OP_WRITE);
    }

}
