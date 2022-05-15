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

public class UpperCaseServer {
    public static void main(String[] args) throws IOException {
        Selector sel = SelectorProvider.provider().openSelector();
        BusinessLogic businessLogic = new BusinessLogic();
        StringConverter stringConverter = new StringConverter();
        businessLogic.setPublisher(stringConverter);

        ServerSocketChannel ss = ServerSocketChannel.open();
        ss.bind(new InetSocketAddress(12345));
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
                        stringConverter.addPublisher(session);
                    }
                }

                if (key.isReadable()) {
                    // New data from client
                    ChatSession session = (ChatSession) key.attachment();
                    ByteBuffer buf = ByteBuffer.allocate(100);
                    SocketChannel ch = (SocketChannel) key.channel();
                    if (ch.read(buf) > 0) {
                        buf.flip();
                        session.handleRead(buf);
                    }
                    else {
                        System.out.println("Client disconnected");
                        key.cancel();
                        session.closedConnection();
                        continue;
                    }

                }

                if (key.isWritable()) {
                    // Client channel available for write
                    ChatSession session = (ChatSession) key.attachment();
                    session.handleWrite();
                }

                i.remove();
            }
        }

    }
}
