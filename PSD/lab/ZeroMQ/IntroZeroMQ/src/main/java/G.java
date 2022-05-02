import org.zeromq.SocketType;
import org.zeromq.ZContext;
import org.zeromq.ZMQ;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;

public class G {
    public static final int nrWorkers = 3;

    public static int g(int x) {
        try {
            Thread.sleep(1000);
        }
        catch (InterruptedException ignored) {}
        return x*x;
    }

    public static void main(String[] args) {
        BlockingQueue<Integer> inputs = new ArrayBlockingQueue<>(100),
                               results = new ArrayBlockingQueue<>(100);
        List<Thread> workers = new ArrayList<>(nrWorkers);
        for (int i = 0; i<nrWorkers; i++) {
            workers.add(new Thread(() -> {
                while(true) {
                    try {
                        int fx = inputs.take();
                        int result = g(fx);
                        results.put(result);
                        System.out.println("Received an f(xi) with value " + fx + " and calculated g(f(xi)): " + result);
                    }
                    catch (InterruptedException ignored) {}
                }
            }));
        }
        for (Thread worker : workers) worker.start();

        try (ZContext context = new ZContext();
             ZMQ.Socket pull_socket = context.createSocket(SocketType.PULL))
        {
            pull_socket.bind("tcp://*:" + args[0]);
            new Thread(() -> {
                try (ZMQ.Socket pub_socket = context.createSocket(SocketType.PUB)) {
                    pub_socket.bind("tcp://*:" + args[1]);
                    while(true){
                        try {
                            pub_socket.send(Integer.toString(results.take()));
                        }
                        catch (InterruptedException ignored) {}
                    }
                }
            }).start();

            while(true) {
                int fx = Integer.parseInt(new String(pull_socket.recv()));
                try {
                    inputs.put(fx);
                }
                catch (InterruptedException ignored) {}
            }
        }
    }
}
