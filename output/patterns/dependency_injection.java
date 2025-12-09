/**
 * Dependency Injection (DI) is a technique whereby one object supplies the dependencies (services)
 * to another object (client).
 * It allows to decouple objects: no need to change client code simply because an object it depends on
 * needs to be changed to a different one. (Open/Closed principle)
 *
 * Port of the Java example of Dependency Injection" in
 * "xUnit Test Patterns - Refactoring Test Code" by Gerard Meszaros
 * (ISBN-10: 0131495054, ISBN-13: 978-0131495050)
 *
 * In the following example `timeProvider` (service) is embedded into TimeDisplay (client).
 * If such service performed an expensive operation you would like to substitute or mock it in tests.
 */

import java.time.LocalDateTime;
import java.util.function.Supplier;

/**
 * Functional interface for time providers
 */
@FunctionalInterface
interface TimeProvider extends Supplier<String> {
}

/**
 * Constructor Injection implementation
 */
class ConstructorInjection {
    private final TimeProvider timeProvider;

    public ConstructorInjection(TimeProvider timeProvider) {
        this.timeProvider = timeProvider;
    }

    public String getCurrentTimeAsHtmlFragment() {
        String currentTime = timeProvider.get();
        return String.format("<span class=\"tinyBoldText\">%s</span>", currentTime);
    }
}

/**
 * Parameter Injection implementation
 */
class ParameterInjection {
    public ParameterInjection() {
        // Default constructor
    }

    public String getCurrentTimeAsHtmlFragment(TimeProvider timeProvider) {
        String currentTime = timeProvider.get();
        return String.format("<span class=\"tinyBoldText\">%s</span>", currentTime);
    }
}

/**
 * Setter Injection implementation
 */
class SetterInjection {
    private TimeProvider timeProvider;

    public SetterInjection() {
        // Default constructor
    }

    public void setTimeProvider(TimeProvider timeProvider) {
        this.timeProvider = timeProvider;
    }

    public String getCurrentTimeAsHtmlFragment() {
        if (timeProvider == null) {
            throw new IllegalStateException("TimeProvider has not been set");
        }
        String currentTime = timeProvider.get();
        return String.format("<span class=\"tinyBoldText\">%s</span>", currentTime);
    }
}

/**
 * Time provider implementations
 */
class TimeProviders {
    /**
     * Production code version of the time provider (just a wrapper for formatting
     * datetime for this example).
     */
    public static String productionCodeTimeProvider() {
        LocalDateTime currentTime = LocalDateTime.now();
        return String.format("%d:%d", currentTime.getHour(), currentTime.getMinute());
    }

    /**
     * Hard-coded stub
     */
    public static String midnightTimeProvider() {
        return "24:01";
    }
}

/**
 * Main class demonstrating dependency injection patterns
 */
public class DependencyInjectionExample {
    public static void main(String[] args) {
        // Constructor Injection examples
        ConstructorInjection timeWithCi1 = new ConstructorInjection(TimeProviders::midnightTimeProvider);
        System.out.println(timeWithCi1.getCurrentTimeAsHtmlFragment());
        // Output: <span class="tinyBoldText">24:01</span>

        ConstructorInjection timeWithCi2 = new ConstructorInjection(TimeProviders::productionCodeTimeProvider);
        System.out.println(timeWithCi2.getCurrentTimeAsHtmlFragment());
        // Output: <span class="tinyBoldText">current_time</span>

        // Parameter Injection example
        ParameterInjection timeWithPi = new ParameterInjection();
        System.out.println(timeWithPi.getCurrentTimeAsHtmlFragment(TimeProviders::midnightTimeProvider));
        // Output: <span class="tinyBoldText">24:01</span>

        // Setter Injection example
        SetterInjection timeWithSi = new SetterInjection();
        
        try {
            timeWithSi.getCurrentTimeAsHtmlFragment();
        } catch (IllegalStateException e) {
            System.out.println("Error: " + e.getMessage());
        }

        timeWithSi.setTimeProvider(TimeProviders::midnightTimeProvider);
        System.out.println(timeWithSi.getCurrentTimeAsHtmlFragment());
        // Output: <span class="tinyBoldText">24:01</span>
    }
}