import java.nio.ByteBuffer;
import java.nio.channels.SelectionKey;
import java.nio.channels.SocketChannel;
import java.util.ArrayDeque;
import java.util.Queue;

public class ChatSession extends SimplePublisher<ByteBuffer> {
    private final SelectionKey key;

    public ChatSession(SelectionKey key) {
        this.key = key;
    }

    public void handleRead(ByteBuffer buf) {
        super.serve(buf);
    }

    public void handleWrite() {
        // ...
    }

    public void closedConnection() {
        super.complete();
    }

}
