public class BusinessLogic implements Subscriber<String> {
    private Publisher<String> pub; // Needs to know publisher to request new items (Flow uses a Subscription class for this purpose)

    public BusinessLogic() {
        this.pub = null;
    }

    public void setPublisher(Publisher<String> strConverter) {
        this.pub = strConverter;
        this.pub.subscribe(this);
        this.pub.request(1);
    }

    public void onNext(String line) {
        System.out.println("New line in upper case: " + line.toUpperCase());
        pub.request(1);
    }

    public void onComplete(Publisher<String> pub) {
        if (pub == this.pub) System.out.println("No client connected!");
    }
}
