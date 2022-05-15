import java.nio.ByteBuffer;
import java.util.*;

public class StringConverter extends SimplePublisher<String> implements Subscriber<ByteBuffer> {
    private List<Publisher<ByteBuffer>> publishers;
    private Queue<String> pendingLines;

    public StringConverter() {
        this.publishers = new ArrayList<>();
        this.pendingLines = new ArrayDeque<>();
    }

    public void addPublisher(Publisher<ByteBuffer> pub) {
        this.publishers.add(pub);
        pub.subscribe(this);
        pub.request(Integer.MAX_VALUE);
    }

    public void onNext(ByteBuffer buf) {
        byte[] tempArray = new byte[buf.remaining()];
        buf.get(tempArray);
        String conversion = new String(tempArray);
        Scanner scanner = new Scanner(conversion);
        while (scanner.hasNextLine()) {
            this.pendingLines.add(scanner.nextLine());
        }
        scanner.close();

        while(super.hasUnfulfilledRequests() && !this.pendingLines.isEmpty()) super.serve(this.pendingLines.remove());

    }

    public void onComplete(Publisher<ByteBuffer> pub) {
        this.publishers.remove(pub);

        if (this.publishers.isEmpty()) super.complete();
    }

}
