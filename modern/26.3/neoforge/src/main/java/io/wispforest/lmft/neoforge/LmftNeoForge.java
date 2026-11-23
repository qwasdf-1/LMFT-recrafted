package io.wispforest.lmft.neoforge;

import io.wispforest.lmft.LmftModern;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.common.Mod;
import net.neoforged.fml.loading.FMLPaths;

@Mod(LmftModern.MOD_ID)
public final class LmftNeoForge {
    public LmftNeoForge(IEventBus bus) {
        LmftModern.init(FMLPaths.CONFIGDIR.get());
    }
}
