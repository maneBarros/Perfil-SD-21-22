import org.zeromq.SocketType;
import org.zeromq.ZMQ;
import org.zeromq.ZContext;

public class F {

  public static int f(int x) {
    try {
      Thread.sleep(1000);
    }
    catch (InterruptedException e) {
      // ignore
    }
    return 2*x;
  }

  public static void main(String[] args) {
    try (ZContext context = new ZContext();
         ZMQ.Socket s = context.createSocket(SocketType.PULL);
         ZMQ.Socket g = context.createSocket(SocketType.PUSH))
    {
      s.connect("tcp://localhost:" + args[0]);
      g.connect("tcp://localhost:" + args[1]);
      while (true) {
          byte[] msg = s.recv();
          int x;
          try {
            x = Integer.parseInt(new String(msg));
          }
          catch (NumberFormatException nf) {
            x = 0;
          }
          System.out.println("Received " + x);
          g.send(Integer.toString(f(x)));
      }
    }
  }
}
