import 'reflect-metadata'
import { Container } from 'inversify'
import { TYPES } from './types'
import { env } from './env'
import { DiscordClient } from './clients/discordClient'
import { TimingClient } from './clients/timingClient'

const iocContainer = new Container()

iocContainer.bind<string>(TYPES.DISCORD_TOKEN).toConstantValue(env.DISCORD_TOKEN)
iocContainer.bind<DiscordClient>(TYPES.DiscordClient).to(DiscordClient).inSingletonScope()
iocContainer.bind<TimingClient>(TYPES.TimingClient).to(TimingClient).inSingletonScope()

export default iocContainer