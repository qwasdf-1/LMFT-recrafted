package io.wispforest.lmft.fabric;

import io.wispforest.lmft.LmftModern;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.loader.api.FabricLoader;

public final class LmftFabric implements ModInitializer {
    @Override
    public void onInitialize() {
        LmftModern.init(FabricLoader.getInstance().getConfigDir());
    }
}
