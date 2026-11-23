package io.wispforest.lmft;

import java.util.List;
import java.util.Objects;
import java.util.function.BiConsumer;
import java.util.stream.Collectors;

/**
 * Loader-independent tag recovery and per-thread tag identity bookkeeping.
 * Tag building occurs during datapack loading/reloading, not every tick.
 */
public final class TagRecovery {
    private static final ThreadLocal<String> CURRENT_TAG = new ThreadLocal<>();
    private static volatile boolean tagsSkipped;

    private TagRecovery() {}

    public static void withTag(String id, Runnable build) {
        Objects.requireNonNull(id, "id");
        Objects.requireNonNull(build, "build");

        // Restore an outer scope if the tag builder is ever called recursively.
        String previous = CURRENT_TAG.get();
        CURRENT_TAG.set(id);
        try {
            build.run();
        } finally {
            if (previous == null) {
                CURRENT_TAG.remove();
            } else {
                CURRENT_TAG.set(previous);
            }
        }
    }

    /**
     * Report and remove unresolved required entries, leaving vanilla's
     * already-resolved values untouched.
     */
    public static void discardMissingEntries(List<?> missing, BiConsumer<String, String> report) {
        if (missing.isEmpty()) {
            return;
        }

        String tag = CURRENT_TAG.get();
        String entries = missing.stream().map(Objects::toString).collect(Collectors.joining(", "));
        report.accept(tag == null ? "lmft:unknown_tag_id" : tag, entries);
        missing.clear();
        tagsSkipped = true;
    }

    public static boolean anyTagsSkipped() {
        return tagsSkipped;
    }

    public static void reset() {
        tagsSkipped = false;
    }

    public static boolean shouldNotify(boolean disabled, boolean onlyOperators, boolean isOperator) {
        return tagsSkipped && !disabled && (!onlyOperators || isOperator);
    }
}
