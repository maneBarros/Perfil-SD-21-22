import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.ByteBuffer;
import java.nio.channels.SelectionKey;
import java.nio.channels.Selector;
import java.nio.channels.ServerSocketChannel;
import java.nio.channels.SocketChannel;
import java.nio.channels.spi.SelectorProvider;
import java.util.Iterator;

public class EchoServer {
    public static void main(String[] args) throws IOException {
        ServerSocketChannel ss = ServerSocketChannel.open();
        ss.bind(new InetSocketAddress(12345));
        Selector sel = SelectorProvider.provider().openSelector();

        ss.configureBlocking(false);
        ss.register(sel, SelectionKey.OP_ACCEPT);
        SocketChannel connectionWithClient = null;
        ByteBuffer buf = ByteBuffer.allocate(100);

        while(true) {
            sel.select();
            //System.out.println("left select!");

            for(Iterator<SelectionKey> i = sel.selectedKeys().iterator(); i.hasNext(); ) {
                SelectionKey key = i.next();

                if (key.isAcceptable()) {
                    System.out.println("acceptable!");
                    connectionWithClient = ss.accept();
                    connectionWithClient.configureBlocking(false);
                    connectionWithClient.register(sel, SelectionKey.OP_READ);
                }

                if (key.isReadable()) {
                    //System.out.println("readable!");
                    if (connectionWithClient.read(buf) <= 0) {
                        System.out.println("connection closed");
                        key.cancel();
                        continue;
                    }
                    else {
                        buf.flip();
                        key.interestOps(SelectionKey.OP_WRITE);
                    }
                }

                if (key.isWritable()) {
                    connectionWithClient.write(buf);
                    buf.clear();
                    key.interestOps(SelectionKey.OP_READ);
                }

                i.remove();
            }
        }



    }
}
