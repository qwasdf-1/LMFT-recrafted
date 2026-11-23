package io.wispforest.lmft.mixin;

import io.wispforest.lmft.TagRecovery;
import net.minecraft.server.MinecraftServer;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import java.util.Collection;
import java.util.concurrent.CompletableFuture;

@Mixin(MinecraftServer.class)
public abstract class MinecraftServerMixin {
    @Inject(method = "reloadResources", at = @At("HEAD"), require = 1)
    private void lmft$resetReloadWarning(
            Collection<String> packs, CallbackInfoReturnable<CompletableFuture<Void>> callback) {
        TagRecovery.reset();
    }
}
