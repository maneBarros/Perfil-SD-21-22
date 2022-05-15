import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.SocketChannel;
import java.util.List;
import java.util.Map;

public class ClientSession implements Runnable{
    private SocketChannel sc;
    private ByteBuffer buf;
    private List<SocketChannel> connections;

    public ClientSession(SocketChannel sc, List<SocketChannel> connections) {
        this.sc = sc;
        this.buf = ByteBuffer.allocate(100);
        this.connections = connections;
    }

    public void run() {
        try {
            while (true) {
                this.sc.read(buf);
                buf.flip();
                for (SocketChannel connection : this.connections) connection.write(buf.duplicate());
                buf.clear();
            }
        }
        catch (IOException e) {
            // ...
        }

    }
}
