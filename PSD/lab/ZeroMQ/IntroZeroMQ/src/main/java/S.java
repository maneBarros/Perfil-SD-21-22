import org.zeromq.SocketType;
import org.zeromq.ZMQ;
import org.zeromq.ZContext;

import java.util.concurrent.locks.ReentrantLock;

public class S {
    private static int h = 0;
    private static final ReentrantLock lock = new ReentrantLock();

    static class AuxWorker implements Runnable {
        private final ZContext context;
        private final String S_port;

        public AuxWorker(ZContext context, String S_port) {
            this.context = context;
            this.S_port = S_port;
        }

        @Override
        public void run() {
            try (ZMQ.Socket sub_socket = context.createSocket(SocketType.SUB)) {
                sub_socket.connect("tcp://localhost:" + S_port);
                sub_socket.subscribe("".getBytes());
                while (true) {
                    int gfx = Integer.parseInt(new String(sub_socket.recv()));
                    System.out.println("Received a new g(f(xi)) value: " + gfx);
                    lock.lock();
                    try {
                        h += gfx;
                    }
                    finally {
                        lock.unlock();
                    }
                }

            }
        }
    }

    public static void main(String[] args) {
        try (ZContext context = new ZContext();
             ZMQ.Socket rep_socket = context.createSocket(SocketType.REP);
             ZMQ.Socket push_socket = context.createSocket(SocketType.PUSH))
        {
            rep_socket.bind("tcp://*:" + args[0]); // Bind reply socket
            push_socket.bind("tcp://*:" + args[1]); // Bind push socket
            new Thread(new AuxWorker(context, args[2])).start();

            while (true) {
                byte[] msg = rep_socket.recv(); // Receives an x
                push_socket.send(msg); // Pushes new x to an F server
                lock.lock();
                try {
                    rep_socket.send(Integer.toString(h)); // Replies to client with current known h value
                }
                finally {
                    lock.unlock();
                }
            }
        }
    }
}
