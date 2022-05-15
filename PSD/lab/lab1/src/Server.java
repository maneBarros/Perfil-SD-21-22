import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.channels.ServerSocketChannel;
import java.nio.channels.SocketChannel;
import java.util.ArrayList;
import java.util.List;

public class Server {
    public static void main(String[] args) throws IOException {
        ServerSocketChannel ss = ServerSocketChannel.open();
        ss.bind(new InetSocketAddress(12345));
        List<SocketChannel> connections = new ArrayList<>();

        while (true) {
            SocketChannel s = ss.accept();
            connections.add(s);
            new Thread(new ClientSession(s, connections)).start();
        }
    }
}
