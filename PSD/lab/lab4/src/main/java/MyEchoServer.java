import spullara.nio.channels.FutureServerSocketChannel;
import spullara.nio.channels.FutureSocketChannel;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.ByteBuffer;
import java.util.Base64;
import java.util.Optional;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;

public class MyEchoServer {
    public static final String username = "mane", password = "12345";

    /*public static CompletableFuture<Void> validateLogin(ByteBuffer buf, FutureSocketChannel socketChannel) {
        return socketChannel.write(ByteBuffer.wrap("Username: ".getBytes()))
                .thenApply(n -> socketChannel.read(buf))
                .thenApply(n -> {
                    buf.flip();
                    byte[] bytes = new byte[buf.remaining()];
                    buf.get(bytes);
                    String insertedUsername = new String(bytes);
                    if (insertedUsername.equals(username)) {
                        socketChannel.write(ByteBuffer.wrap("Password: ".getBytes()));
                        buf.reset();
                        socketChannel.read(buf);
                        buf.flip();
                        bytes = new byte[buf.remaining()];
                        buf.get(bytes);
                        String insertedPassword = new String(bytes);
                        if (insertedPassword.equals(password)) {
                            socketChannel.write(ByteBuffer.wrap("Logged in!".getBytes()));
                            buf.reset();
                            return true;
                        }
                        else {
                            socketChannel.write(ByteBuffer.wrap("Wrong password!\n".getBytes()));
                            return false;
                        }
                    } else {
                        socketChannel.write(ByteBuffer.wrap("Wrong username!\n".getBytes()));
                        return false;
                    }
                });
    } */

    public static CompletableFuture<Void> echoes(ByteBuffer buf, FutureSocketChannel socketChannel) {
        return socketChannel.read(buf)
                .thenCompose(n -> {
                    buf.flip();
                    var r = socketChannel.write(buf);
                    buf.flip();
                    return r;
                })
                .thenRun(() -> echoes(buf, socketChannel));
    }

    public static CompletableFuture<Void> acceptsClients(FutureServerSocketChannel serverSocketChannel) {
        ByteBuffer buf = ByteBuffer.allocate(100);
        return serverSocketChannel.accept()
                .thenApply(s -> {
                    System.out.println("New client!");
                    return s;
                })
                .thenAccept(s -> echoes(buf, s))
                .thenCompose(n -> acceptsClients(serverSocketChannel));

    }
    public static void main(String[] args) throws IOException, InterruptedException, ExecutionException {
        FutureServerSocketChannel serverSocketChannel = new FutureServerSocketChannel();
        serverSocketChannel.bind(new InetSocketAddress("localhost",12345));
        acceptsClients(serverSocketChannel).get();
    }
}
