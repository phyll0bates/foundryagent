package org.apache.log4j;

public class Logger {
    private final String name;

    private Logger(String name) {
        this.name = name;
    }

    public static Logger getLogger(Class<?> cls) {
        return new Logger(cls.getSimpleName());
    }

    public void info(String msg) {
        System.out.println("INFO [" + name + "]: " + msg);
    }
}
