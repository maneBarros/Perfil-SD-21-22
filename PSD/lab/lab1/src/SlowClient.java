import java.io.*;
import java.net.Socket;

public class SlowClient {
    final static int delayWrites = 5000,
                     delayReads = 10000;

    public static void main(String[] args) throws IOException {
        Socket socket = new Socket("localhost",12345);
        DataInputStream dis = new DataInputStream(new BufferedInputStream(socket.getInputStream()));
        DataOutputStream dos = new DataOutputStream(new BufferedOutputStream(socket.getOutputStream()));


        // Thread that reads incoming messages
        new Thread(() -> {
            while(true) {
                try {
                    System.out.println(dis.readUTF());
                    Thread.sleep(delayReads);
                }
                catch (Exception ignored) {}
            }
        }).start();

        // Thread that writes messages
        new Thread(() -> {
            while(true) {
                try {
                    dos.writeUTF("Message from slow client\n");
                    dos.flush();
                    Thread.sleep(delayWrites);
                }
                catch (Exception e) {}
            }

        }).start();

    }
}
