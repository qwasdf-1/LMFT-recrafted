package io.wispforest.lmft.mixin;

import com.llamalad7.mixinextras.injector.wrapoperation.Operation;
import com.llamalad7.mixinextras.injector.wrapoperation.WrapOperation;
import io.wispforest.lmft.LmftModern;
import io.wispforest.lmft.TagRecovery;
import net.minecraft.resources.Identifier;
import net.minecraft.tags.TagLoader;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.ModifyArg;

import java.util.List;
import java.util.function.BiConsumer;

@Mixin(value = TagLoader.class, priority = 800)
public abstract class TagLoaderMixin {
    /**
     * The 26.3 implementation still tests the unresolved-entry list before
     * returning Either.left or Either.right. Preserve all resolved entries.
     */
    @WrapOperation(
        method = "tryBuildTag(Lnet/minecraft/tags/TagEntry$Lookup;Ljava/util/List;)Lcom/mojang/datafixers/util/Either;",
        at = @At(value = "INVOKE", target = "Ljava/util/List;isEmpty()Z"),
        require = 1,
        allow = 1
    )
    private boolean lmft$keepValidEntries(List<?> missing, Operation<Boolean> original) {
        LmftModern.handleInvalidEntries(missing);
        return original.call(missing);
    }

    /**
     * Unlike a lambda$build$N HEAD injection, this callback wrapper does not
     * depend on Mojang's synthetic lambda numbering. The per-tag scope also
     * clears thread-local state on successful builds and exceptions.
     */
    @ModifyArg(
        method = "build(Ljava/util/Map;)Ljava/util/Map;",
        at = @At(
            value = "INVOKE",
            target = "Lnet/minecraft/util/DependencySorter;orderByDependencies(Ljava/util/function/BiConsumer;)V"
        ),
        index = 0,
        require = 1,
        allow = 1
    )
    private BiConsumer<Identifier, Object> lmft$wrapTagBuilder(
            BiConsumer<Identifier, Object> original) {
        return (id, contents) -> TagRecovery.withTag(id.toString(), () ->
            original.accept(id, contents));
    }
}
