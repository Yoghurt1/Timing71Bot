import 'reflect-metadata'
import { Client } from 'discordx'
import { Intents } from 'discord.js'
import { inject, injectable } from 'inversify'
import { TYPES } from '../types'

@injectable()
export class DiscordClient {
  public client = new Client({
    intents: [
      Intents.FLAGS.GUILDS,
      Intents.FLAGS.GUILD_MESSAGES,
      Intents.FLAGS.GUILD_MESSAGE_REACTIONS,
      Intents.FLAGS.DIRECT_MESSAGES,
      Intents.FLAGS.GUILD_PRESENCES
    ],
    prefix: '.',
    silent: false,
    classes: [`${__dirname}/commands/*.{js,ts}`]
  })

  constructor(
    @inject(TYPES.DISCORD_TOKEN) private readonly token: string
  ) { }

  public async start(): Promise<void> {
    await this.client.login(this.token)
  }
}
