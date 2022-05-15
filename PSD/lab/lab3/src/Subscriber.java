public interface Subscriber<T> {
    void onNext(T data);
    void onComplete(Publisher<T> pub);
}
