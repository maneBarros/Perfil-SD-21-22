import java.io.*;
import java.net.Socket;

public class NormalClient {
    final static int delayWrites = 2000;

    public static void main(String[] args) throws IOException {
        Socket socket = new Socket("localhost",12345);
        DataInputStream dis = new DataInputStream(new BufferedInputStream(socket.getInputStream()));
        DataOutputStream dos = new DataOutputStream(new BufferedOutputStream(socket.getOutputStream()));
        Thread reader, writer;


        // Thread that reads incoming messages
        reader = new Thread(() -> {
            while(true) {
                try {
                    System.out.println(dis.readUTF());
                }
                catch (Exception ignored) {}
            }
        });

        // Thread that writes messages
        writer = new Thread(() -> {
            while(true) {
                try {
                    dos.writeUTF("Message from slow client\n");
                    dos.flush();
                    Thread.sleep(delayWrites);
                }
                catch (Exception e) {}
            }
        });

        reader.start(); writer.start();

        try {
            reader.join();
            writer.join();
        }
        catch (InterruptedException e) {}

        socket.close();

    }
}
