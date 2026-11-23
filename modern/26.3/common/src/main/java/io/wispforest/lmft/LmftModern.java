package io.wispforest.lmft;

import com.mojang.logging.LogUtils;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.ClickEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.permissions.Permissions;
import org.slf4j.Logger;

import java.net.URI;
import java.nio.file.Path;
import java.util.List;

public final class LmftModern {
    public static final String MOD_ID = "lmft";
    public static final String PREFIX = "[Load My F***ing Tags]: ";
    public static final Logger LOGGER = LogUtils.getLogger();

    private static final URI INFO_URL =
        URI.create("https://github.com/qwasdf-1/LMFT-recrafted/blob/1.21.x/info.md");
    private static volatile LmftConfig.Settings settings = LmftConfig.Settings.DEFAULT;

    private LmftModern() {}

    public static void init(Path configDirectory) {
        settings = LmftConfig.load(configDirectory);
        LOGGER.info("LMFT 26.3 initialized");
    }

    public static void handleInvalidEntries(List<?> missing) {
        TagRecovery.discardMissingEntries(missing, (id, entries) ->
            LOGGER.warn("{}Couldn't load certain entries within tag {}: {}", PREFIX, id, entries));
    }

    public static void notifyPlayer(ServerPlayer player) {
        LmftConfig.Settings current = settings;
        boolean disabled = current.disableIngameError() || Boolean.getBoolean("lmft.disable_error_output");
        boolean moderator = player.permissions().hasPermission(Permissions.COMMANDS_MODERATOR);
        if (!TagRecovery.shouldNotify(disabled, current.showToOnlyPrivileged(), moderator)) {
            return;
        }

        player.sendSystemMessage(
            Component.literal(PREFIX).withStyle(ChatFormatting.RED, ChatFormatting.BOLD)
                .append(Component.translatableWithFallback(
                    "lmft.cooked_tags_message",
                    "Some tag entries were skipped; see the server log for the missing references."
                ).withStyle(ChatFormatting.RED))
                .append(Component.literal(" "))
                .append(Component.translatableWithFallback(
                    "lmft.cooked_tags_link_message", "Click for more information."
                ).withStyle(ChatFormatting.AQUA)
                    .withStyle(style -> style.withClickEvent(new ClickEvent.OpenUrl(INFO_URL))))
        );
    }
}
