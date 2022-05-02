import org.zeromq.SocketType;
import org.zeromq.ZMQ;
import org.zeromq.ZContext;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;

public class Client {
    public static void main(String[] args) {
        try (ZContext context = new ZContext();
             ZMQ.Socket socket = context.createSocket(SocketType.REQ))
        {
            socket.connect("tcp://localhost:" + args[0]);
            BufferedReader obj = new BufferedReader(new InputStreamReader(System.in));
            while (true) {
                try {
                    String str = obj.readLine();
                    if (str == null) break;
                    socket.send(str);
                    byte[] msg = socket.recv();
                    System.out.println("Current h value is " + new String(msg));
                }
                catch (IOException ioe) {
                    System.out.println("error while reading from stdin");
                }
            }
        }
    }
}
