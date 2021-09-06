import 'reflect-metadata'
import { Connection, Session } from 'autobahn'
import { inject, injectable } from 'inversify'
import { TYPES } from '../types'
import { DiscordClient } from './discordClient'
import axios from 'axios'
import { ServiceManifest } from '../models/serviceManifest'

@injectable()
export class TimingClient {
  constructor(
    @inject(TYPES.DiscordClient) private discordClient: DiscordClient
  ) { }

  public async start() {
    const connection = new Connection({
      url: await this.getRelay(),
      realm: "timing"
    })

    connection.onopen = this.main

    connection.open()
    this.discordClient.start()
  }

  private async main(session: Session): Promise<void> {
    const self = this
    let _events: ServiceManifest[]
    let _currentEvent: ServiceManifest

    function eventsHandler(response) {
      _events = JSON.parse(response["payload"])
      
      const currentEvents: string[] = []

      for (const [index, event] of _events.entries()) {
        const eventString: string = `${index + 1}. ${event.name} - ${event.description}`
        currentEvents.push(eventString)
      }

      if (!_events.includes(_currentEvent)) {
        let msg = "New event(s) started:\n"
        msg = `${msg}\nUse the reacts below for each event number if you want to connect.${currentEvents.join("\n")}`

        self.discordClient.client.channels.fetch("767481691529805846")
      }
    }

    session.subscribe("livetiming.directory", eventsHandler, { get_retained: true })
    
  }

  private async getRelay(): Promise<string> {
    const res = await axios.get("https://www.timing71.org/relays")
    
    const relays = JSON.parse(res.data)["args"]
    return Object.keys(relays)[0]
  }
}