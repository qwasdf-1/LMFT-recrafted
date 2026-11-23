package io.wispforest.lmft.mixin;

import io.wispforest.lmft.LmftModern;
import net.minecraft.network.Connection;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.network.CommonListenerCookie;
import net.minecraft.server.players.PlayerList;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(PlayerList.class)
public abstract class PlayerListMixin {
    // Run after login completes, rather than depending on packet NEW targets.
    @Inject(method = "placeNewPlayer", at = @At("TAIL"), require = 1)
    private void lmft$onPlayerJoined(
            Connection connection, ServerPlayer player, CommonListenerCookie cookie, CallbackInfo ci) {
        LmftModern.notifyPlayer(player);
    }

    @Inject(method = "reloadResources", at = @At("TAIL"), require = 1)
    private void lmft$onDatapackReload(CallbackInfo ci) {
        ((PlayerList) (Object) this).getPlayers().forEach(LmftModern::notifyPlayer);
    }
}
