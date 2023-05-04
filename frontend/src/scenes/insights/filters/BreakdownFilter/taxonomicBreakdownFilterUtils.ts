import { BreakdownType, FilterType, PropertyDefinition, TrendsFilterType } from '~/types'
import {
    TaxonomicFilterGroup,
    TaxonomicFilterGroupType,
    TaxonomicFilterValue,
} from 'lib/components/TaxonomicFilter/types'
import { taxonomicFilterTypeToPropertyFilterType } from 'lib/components/PropertyFilters/utils'

export const isAllCohort = (t: number | string): t is string => typeof t === 'string' && t == 'all'

export const isCohort = (t: number | string): t is number => typeof t === 'number'

export const isCohortBreakdown = (t: number | string): t is number | string => isAllCohort(t) || isCohort(t)

export const isPersonEventOrGroup = (t: number | string): t is string => typeof t === 'string' && t !== 'all'

export const isURLNormalizeable = (propertyName: string): boolean => {
    return ['$current_url', '$pathname'].includes(propertyName)
}
interface FilterChange {
    useMultiBreakdown: string | boolean | undefined
    breakdownParts: (string | number)[]
    setFilters: (filters: Partial<FilterType>, mergeFilters?: boolean) => void
    getPropertyDefinition: (propertyName: string | number) => PropertyDefinition | null
}

export function onAddBreakdown({ useMultiBreakdown, breakdownParts, setFilters, getPropertyDefinition }: FilterChange) {
    return (changedBreakdown: TaxonomicFilterValue, taxonomicGroup: TaxonomicFilterGroup): void => {
        const changedBreakdownType = taxonomicFilterTypeToPropertyFilterType(taxonomicGroup.type) as BreakdownType

        if (changedBreakdownType) {
            const isHistogramable = !useMultiBreakdown && !!getPropertyDefinition(changedBreakdown)?.is_numerical

            const newFilters: Partial<TrendsFilterType> = {
                breakdown_type: changedBreakdownType,
                breakdown_group_type_index: taxonomicGroup.groupTypeIndex,
                breakdown_histogram_bin_count: isHistogramable ? 10 : undefined,
                // if property definitions are not loaded when this runs then a normalizeable URL will not be normalized.
                // For now, it is safe to fall back to `changedBreakdown`
                breakdown_normalize_url: isURLNormalizeable(
                    getPropertyDefinition(changedBreakdown)?.name || (changedBreakdown as string)
                ),
            }

            if (useMultiBreakdown) {
                newFilters.breakdowns = [...breakdownParts, changedBreakdown]
                    .filter((b): b is string | number => !!b)
                    .map((b) => ({
                        property: b,
                        type: changedBreakdownType,
                        normalize_url: isURLNormalizeable(b.toString()),
                    }))
            } else {
                newFilters.breakdown =
                    taxonomicGroup.type === TaxonomicFilterGroupType.CohortsWithAllUsers
                        ? [...breakdownParts, changedBreakdown].filter((b): b is string | number => !!b)
                        : changedBreakdown
            }

            setFilters(newFilters, true)
        }
    }
}
