import spullara.nio.channels.FutureServerSocketChannel;
import spullara.nio.channels.FutureSocketChannel;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.ByteBuffer;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;

public class MyEchoServer2 {
    public static CompletableFuture<Void> echoes(LineBuffer lb) {
        return lb.readLine()
                .thenCompose(lb::writeLine)
                .thenRun(() -> echoes(lb));    // Quando exatamente devo usar thenCompose? O prof no exemplo usava aqui thenRun().
                                               // Pelas explicações da net parece fazer mais sentido o compose, já que echoes retorna um completablefuture
    }

    public static CompletableFuture<Void> handlesNewClient(LoginValid validation) {
        return validation
                .nextClient()
                .thenAccept(MyEchoServer2::echoes)
                .thenCompose(x -> handlesNewClient(validation));
    }

    public static void main(String[] args) throws IOException, InterruptedException, ExecutionException {
        FutureServerSocketChannel serverSocketChannel = new FutureServerSocketChannel();
        serverSocketChannel.bind(new InetSocketAddress("localhost",12345));
        LoginValid validation = new LoginValid(serverSocketChannel);

        handlesNewClient(validation).get();
    }
}
