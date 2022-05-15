public abstract class SimplePublisher<T> implements Publisher<T> {
    private Subscriber<T> sub;
    private int unfulfilled_requests;

    public void subscribe(Subscriber<T> sub) {
        this.sub = sub;
        this.unfulfilled_requests = 0;
    }

    public void request(int n) {
        if (this.sub != null && n > 0) {
            if (this.unfulfilled_requests == Integer.MAX_VALUE || n == Integer.MAX_VALUE) this.unfulfilled_requests = Integer.MAX_VALUE;
            else this.unfulfilled_requests += n;
        }
    }

    public void cancel() {
        this.sub = null;
        this.unfulfilled_requests = 0;
    }

    public boolean hasUnfulfilledRequests() {return unfulfilled_requests > 0;}

    public void serve(T item) {
        if (unfulfilled_requests > 0) {
            this.sub.onNext(item);
            if (unfulfilled_requests != Integer.MAX_VALUE) unfulfilled_requests--;
        }
    }

    public void complete() {this.sub.onComplete(this);}
}
