import 'reflect-metadata'
import iocContainer from './ioc'
import { TimingClient } from './clients/timingClient'
import { TYPES } from './types'

const client: TimingClient = iocContainer.get<TimingClient>(TYPES.TimingClient)

client.start()