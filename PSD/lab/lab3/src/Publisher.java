public interface Publisher<T> {
    void subscribe(Subscriber<T> sub);
    void request(int n);
    void cancel();

}
