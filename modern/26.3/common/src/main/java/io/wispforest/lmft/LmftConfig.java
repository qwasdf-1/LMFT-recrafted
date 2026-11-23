package io.wispforest.lmft;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

/** Retains the original config filename and keys for drop-in upgrades. */
public final class LmftConfig {
    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();

    public record Settings(boolean disableIngameError, boolean showToOnlyPrivileged) {
        public static final Settings DEFAULT = new Settings(false, false);
    }

    private LmftConfig() {}

    public static Settings load(Path configDirectory) {
        Path configFile = configDirectory.resolve("lmft.json");
        try {
            Files.createDirectories(configDirectory);
            if (Files.notExists(configFile)) {
                JsonObject defaults = new JsonObject();
                defaults.addProperty("disableIngameError", false);
                defaults.addProperty("showToOnlyPrivileged", false);
                Files.writeString(configFile, GSON.toJson(defaults));
                return Settings.DEFAULT;
            }

            JsonObject object = JsonParser.parseString(Files.readString(configFile)).getAsJsonObject();
            boolean disable = booleanOrDefault(object, "disableIngameError", false);
            boolean privileged = booleanOrDefault(object, "showToOnlyPrivileged", false);
            return new Settings(disable, privileged);
        } catch (IOException | RuntimeException exception) {
            LmftModern.LOGGER.warn("LMFT: Unable to load {}, using defaults", configFile, exception);
            return Settings.DEFAULT;
        }
    }

    private static boolean booleanOrDefault(JsonObject object, String key, boolean fallback) {
        return object.has(key) && !object.get(key).isJsonNull()
            ? object.get(key).getAsBoolean() : fallback;
    }
}
