import { actions, kea, listeners, path, reducers } from 'kea'
import { teamLogic } from 'scenes/teamLogic'

import type { maxLogicType } from './maxLogicType'

export const maxLogic = kea<maxLogicType>([
    path(['scenes', 'max', 'maxLogic']),
    actions({
        askMax: (prompt: string) => ({ prompt }),
        addMessage: (message: any) => ({ message }),
        replaceMessages: (messages: any) => ({ messages }),
    }),
    reducers({
        thread: [
            [] as any[],
            {
                addMessage: (state, { message }) => {
                    return [...state, message]
                },
                replaceMessages: (_, { messages }) => {
                    return messages
                },
            },
        ],
    }),
    listeners(({ actions, values: { thread } }) => ({
        askMax: ({ prompt }) =>
            new Promise<void>((resolve) => {
                const url = new URL(`/api/projects/${teamLogic.values.currentTeamId}/query/chat/`, location.origin)
                url.searchParams.append('prompt', prompt)
                url.searchParams.append('thread', JSON.stringify(thread.slice(1)))
                const source = new window.EventSource(url.toString())
                source.onerror = (e) => {
                    console.error('Failed to poll chat: ', e)
                }
                source.onmessage = (event: any) => {
                    const eventData = JSON.parse(event.data)

                    if (!Object.keys(eventData).length) {
                        // An empty object is the termination signal
                        source.close()
                        resolve()
                    } else {
                        actions.replaceMessages(eventData)
                    }
                }
            }),
    })),
])
