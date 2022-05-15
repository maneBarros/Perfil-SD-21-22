import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.ByteBuffer;
import java.nio.channels.SelectionKey;
import java.nio.channels.Selector;
import java.nio.channels.ServerSocketChannel;
import java.nio.channels.SocketChannel;
import java.nio.channels.spi.SelectorProvider;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

public class SelectorServer {
    public static void main(String[] args) throws IOException {
        ServerSocketChannel ss = ServerSocketChannel.open();
        ss.bind(new InetSocketAddress(12345));
        Selector sel = SelectorProvider.provider().openSelector();
        List<ChatSession> sessions = new ArrayList<>();

        ss.configureBlocking(false);
        ss.register(sel, SelectionKey.OP_ACCEPT);

        while (true) {
            sel.select();

            for(Iterator<SelectionKey> i = sel.selectedKeys().iterator(); i.hasNext(); ) {
                SelectionKey key = i.next();

                if (key.isAcceptable()) {
                    // New client connection
                    SocketChannel clientSocket = ss.accept();

                    if (clientSocket != null) {
                        clientSocket.configureBlocking(false);
                        SelectionKey keyForClient = clientSocket.register(sel, SelectionKey.OP_READ);
                        ChatSession session = new ChatSession(keyForClient);
                        keyForClient.attach(session);
                        sessions.add(session);
                    }
                }

                if (key.isReadable()) {
                    // New data from client
                    System.out.println("Readable!");
                    ByteBuffer buf = ByteBuffer.allocate(100);
                    SocketChannel ch = (SocketChannel) key.channel();
                    ch.read(buf);
                    buf.flip();
                    for (ChatSession session : sessions) session.addMessage(buf.duplicate());
                }

                if (key.isWritable()) {
                    // Client channel available for write
                    System.out.println("Writable!");
                    SocketChannel ch = (SocketChannel) key.channel();
                    ChatSession session = (ChatSession) key.attachment();
                    ch.write(session.getMessage());
                }

                i.remove();
            }
        }
    }
}
