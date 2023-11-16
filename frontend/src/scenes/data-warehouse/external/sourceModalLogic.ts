import { actions, connect, kea, path, reducers, selectors, listeners } from 'kea'

import type { sourceModalLogicType } from './sourceModalLogicType'
import { forms } from 'kea-forms'
import { ExternalDataSourceCreatePayload } from '~/types'
import api from 'lib/api'
import { lemonToast } from '@posthog/lemon-ui'
import { dataWarehouseTableLogic } from '../new_table/dataWarehouseTableLogic'
import { dataWarehouseSceneLogic } from './dataWarehouseSceneLogic'
import { router } from 'kea-router'
import { urls } from 'scenes/urls'
import { dataWarehouseSettingsLogic } from '../settings/dataWarehouseSettingsLogic'
import stripeLogo from 'public/stripe-logo.svg'
import postgresLogo from 'public/postgres-logo.svg'

export interface ConnectorConfigType {
    name: string
    caption: string
    disabledReason: string | null
    icon: string
}

// TODO: add icon
export const CONNECTORS: ConnectorConfigType[] = [
    {
        name: 'stripe',
        caption: 'Enter your Stripe credentials to link your Stripe to PostHog',
        disabledReason: null,
        icon: stripeLogo,
    },
    {
        name: 'postgres',
        caption: 'Enter your Postgres credentials to link your Postgres database to PostHog',
        disabledReason: null,
        icon: postgresLogo,
    },
]

type FormTypes = 'input' | 'select'

export interface FormPayloadType {
    name: string
    type: FormTypes
    label: string
}

export const FORM_PAYLOAD_TYPES: Record<string, FormPayloadType[]> = {
    stripe: [
        {
            name: 'account_id',
            type: 'input',
            label: 'Account Id',
        },
        {
            name: 'client_secret',
            type: 'input',
            label: 'Client Secret',
        },
    ],
    postgres: [
        {
            name: 'host',
            type: 'input',
            label: 'Host',
        },
        {
            name: 'port',
            type: 'input',
            label: 'Port',
        },
        {
            name: 'database',
            type: 'input',
            label: 'Database',
        },
        {
            name: 'username',
            type: 'input',
            label: 'Username',
        },
        {
            name: 'password',
            type: 'input',
            label: 'Password',
        },
    ],
}

export const sourceModalLogic = kea<sourceModalLogicType>([
    path(['scenes', 'data-warehouse', 'external', 'sourceModalLogic']),
    actions({
        selectConnector: (connector: ConnectorConfigType | null) => ({ connector }),
        toggleManualLinkFormVisible: (visible: boolean) => ({ visible }),
    }),
    connect({
        values: [dataWarehouseTableLogic, ['tableLoading'], dataWarehouseSettingsLogic, ['dataWarehouseSources']],
        actions: [
            dataWarehouseSceneLogic,
            ['toggleSourceModal'],
            dataWarehouseTableLogic,
            ['resetTable'],
            dataWarehouseSettingsLogic,
            ['loadSources'],
        ],
    }),
    reducers({
        selectedConnector: [
            null as ConnectorConfigType | null,
            {
                selectConnector: (_, { connector }) => connector,
            },
        ],
        isManualLinkFormVisible: [
            false,
            {
                toggleManualLinkFormVisible: (_, { visible }) => visible,
            },
        ],
    }),
    selectors({
        showFooter: [
            (s) => [s.selectedConnector, s.isManualLinkFormVisible],
            (selectedConnector, isManualLinkFormVisible) => selectedConnector || isManualLinkFormVisible,
        ],
        connectors: [
            (s) => [s.dataWarehouseSources],
            (sources) => {
                return CONNECTORS.map((connector) => ({
                    ...connector,
                    disabledReason:
                        sources && sources.results.find((source) => source.source_type === connector.name)
                            ? 'Already linked'
                            : null,
                }))
            },
        ],
    }),
    forms(() => ({
        externalDataSource: {
            defaults: { account_id: '', client_secret: '' },
            errors: ({ account_id, client_secret }) => {
                return {
                    account_id: !account_id && 'Please enter an account id.',
                    client_secret: !client_secret && 'Please enter a client secret.',
                }
            },
            submit: async (payload) => {
                await api.externalDataSources.create({
                    payload,
                    payload_type: 'stripe',
                } as ExternalDataSourceCreatePayload)
                return payload
            },
        },
    })),
    listeners(({ actions }) => ({
        submitExternalDataSourceSuccess: () => {
            lemonToast.success('New Data Resource Created')
            actions.toggleSourceModal()
            actions.resetExternalDataSource()
            actions.loadSources()
            router.actions.push(urls.dataWarehouseSettings())
        },
        submitExternalDataSourceFailure: () => {
            lemonToast.error('Error creating new Data Resource. Check that provided credentials are valid.')
        },
    })),
])
