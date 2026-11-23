package io.wispforest.lmft;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicReference;

/** Plain-Java smoke tests: no Minecraft runtime or testing framework required. */
public final class TagRecoveryTest {
    private TagRecoveryTest() {}

    public static void main(String[] args) {
        TagRecovery.reset();
        List<String> valid = new ArrayList<>(List.of("minecraft:stone"));
        List<String> empty = new ArrayList<>();
        TagRecovery.withTag("lmft_test:ok", () ->
            TagRecovery.discardMissingEntries(empty, (tag, missing) -> fail("unexpected warning")));
        assertTrue(!TagRecovery.anyTagsSkipped(), "valid tag must not set warning state");

        AtomicReference<String> loggedTag = new AtomicReference<>();
        List<String> missing = new ArrayList<>(List.of("lmft_test:missing_block"));
        TagRecovery.withTag("lmft_test:recovery", () ->
            TagRecovery.discardMissingEntries(missing, (tag, entries) -> loggedTag.set(tag)));
        assertEquals("lmft_test:recovery", loggedTag.get(), "correct tag ID");
        assertTrue(missing.isEmpty(), "missing entries cleared");
        assertEquals(1, valid.size(), "resolved entries retained");
        assertTrue(TagRecovery.anyTagsSkipped(), "warning state recorded");

        loggedTag.set(null);
        TagRecovery.discardMissingEntries(new ArrayList<>(List.of("another:missing")),
            (tag, entries) -> loggedTag.set(tag));
        assertEquals("lmft:unknown_tag_id", loggedTag.get(), "no stale tag ID");

        TagRecovery.withTag("outer:tag", () -> {
            TagRecovery.withTag("inner:tag", () -> {});
            TagRecovery.discardMissingEntries(new ArrayList<>(List.of("x")),
                (tag, entries) -> loggedTag.set(tag));
        });
        assertEquals("outer:tag", loggedTag.get(), "nested scope restored");

        try {
            TagRecovery.withTag("throws:tag", () -> { throw new IllegalStateException("expected"); });
            fail("expected exception");
        } catch (IllegalStateException expected) {
            // Finally must clear the thread context.
        }
        TagRecovery.discardMissingEntries(new ArrayList<>(List.of("x")),
            (tag, entries) -> loggedTag.set(tag));
        assertEquals("lmft:unknown_tag_id", loggedTag.get(), "exception cleanup");

        assertTrue(TagRecovery.shouldNotify(false, false, false), "ordinary warning");
        assertTrue(!TagRecovery.shouldNotify(false, true, false), "non-operator excluded");
        assertTrue(TagRecovery.shouldNotify(false, true, true), "operator included");
        assertTrue(!TagRecovery.shouldNotify(true, false, true), "disabled warning");

        TagRecovery.reset();
        assertTrue(!TagRecovery.anyTagsSkipped(), "reset removes warning state");
        System.out.println("TagRecoveryTest: all assertions passed");
    }

    private static void assertTrue(boolean result, String message) {
        if (!result) throw new AssertionError(message);
    }

    private static void assertEquals(Object expected, Object actual, String message) {
        if (!java.util.Objects.equals(expected, actual))
            throw new AssertionError(message + ": expected " + expected + ", got " + actual);
    }

    private static void fail(String message) {
        throw new AssertionError(message);
    }
}
