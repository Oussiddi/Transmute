import java.util.HashMap;
import java.util.Map;

/**
 * The Borg design pattern - all instances share the same state.
 * 
 * This is useful when you want multiple instances to share data
 * but don't want to use a Singleton.
 */
class Borg {
    protected static Map<String, Object> sharedState = new HashMap<>();

    public Borg() {
        // In Java, we can't directly assign the instance's field map like Python's __dict__
        // Instead, we'll use getter/setter methods to access the shared state
    }

    protected Object getSharedProperty(String key) {
        return sharedState.get(key);
    }

    protected void setSharedProperty(String key, Object value) {
        sharedState.put(key, value);
    }

    @Override
    public String toString() {
        return sharedState.toString();
    }
}

/**
 * Example subclass of Borg.
 */
class YourBorg extends Borg {
    private static final String STATE_KEY = "state";

    public YourBorg() {
        this(null);
    }

    public YourBorg(String state) {
        super();
        if (state != null) {
            setState(state);
        } else {
            if (getState() == null) {
                setState("Init");
            }
        }
    }

    public String getState() {
        return (String) getSharedProperty(STATE_KEY);
    }

    public void setState(String state) {
        setSharedProperty(STATE_KEY, state);
    }

    @Override
    public String toString() {
        return String.format("YourBorg with state: %s", getState());
    }
}

public class BorgPatternDemo {
    /**
     * Demonstrate the Borg pattern.
     */
    public static void main(String[] args) {
        YourBorg rm1 = new YourBorg();
        YourBorg rm2 = new YourBorg();

        rm1.setState("Idle");
        rm2.setState("Running");

        System.out.println("rm1: " + rm1);
        System.out.println("rm2: " + rm2);

        // Both should have 'Running' state
        YourBorg rm3 = new YourBorg();
        System.out.println("rm3: " + rm3);
    }
}