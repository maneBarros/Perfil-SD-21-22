import spullara.nio.channels.FutureServerSocketChannel;
import spullara.nio.channels.FutureSocketChannel;

import java.util.Objects;
import java.util.concurrent.CompletableFuture;

public class LoginValid {
    public static final String username = "mane", password = "12345";
    private final FutureServerSocketChannel serverSocketChannel;

    public LoginValid(FutureServerSocketChannel serverSocketChannel) {
        this.serverSocketChannel = serverSocketChannel;
    }

    private CompletableFuture<Boolean> validatePassword(LineBuffer lb) {
        return lb
                .writeLine("Password: ")
                .thenCompose(n -> lb.readLine())
                .thenApply(s -> s.trim().equals(password))
                .thenCompose(b -> b ? CompletableFuture.completedFuture(true) : lb.writeLine("Wrong password\n").thenApply(n -> false));
    }

    private CompletableFuture<Boolean> validateLogin(LineBuffer lb) {
        return lb
                .writeLine("Username: ")
                .thenCompose(n -> lb.readLine())
                .thenApply(s -> s.trim().equals(username))
                .thenCompose(b -> b ? validatePassword(lb) : lb.writeLine("Username not found\n").thenApply(n -> false));
    }

    public CompletableFuture<LineBuffer> nextClient() {
        CompletableFuture<LineBuffer> futureLineBuffer = this.serverSocketChannel.accept().thenApply(LineBuffer::new);

        return futureLineBuffer
                .thenCompose(this::validateLogin)
                .thenCompose(b -> {
                    if (b) return futureLineBuffer;
                    else {
                        return futureLineBuffer
                                .thenAccept(LineBuffer::close)
                                .thenCompose(n -> nextClient());
                    }
                });
    }
}
