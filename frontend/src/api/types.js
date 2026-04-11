/**
 * API Types — Phase B
 *
 * JSDoc typedefs for UI view-model objects used across pages and components.
 * No runtime code — import this file only for editor type support.
 */

/**
 * @typedef {'loading'|'success'|'empty'|'error'} UIStateVariant
 */

/**
 * @typedef {Object} UIState
 * @property {UIStateVariant} state
 * @property {*} data
 * @property {string|null} error
 * @property {boolean} isDemo
 */

/**
 * @typedef {Object} SummaryCard
 * @property {string} id
 * @property {string} label
 * @property {number|string} value
 * @property {string} unit
 * @property {number|null} trend
 * @property {string|null} trendLabel
 * @property {'up'|'down'|'neutral'|null} trendDirection
 * @property {string|null} icon
 */

/**
 * @typedef {Object} ChartPoint
 * @property {string} date
 * @property {number} value
 * @property {number|null} upper
 * @property {number|null} lower
 * @property {string|null} category
 */

/**
 * @typedef {Object} AlertItem
 * @property {string} id
 * @property {string} title
 * @property {string} message
 * @property {'info'|'warning'|'danger'} severity
 * @property {string} timestamp
 * @property {string|null} actionLabel
 * @property {string|null} actionUrl
 */

/**
 * @typedef {Object} SimulatorResultMarketing
 * @property {number} adWeeksBefore
 * @property {number} earlybirdDays
 * @property {number} discountRate
 */

/**
 * @typedef {Object} SimulatorResultOperations
 * @property {number} instructors
 * @property {number} classrooms
 */

/**
 * @typedef {Object} ScenarioItem
 * @property {string} scenario
 * @property {number} predicted_enrollment
 * @property {'High'|'Mid'|'Low'} demand_tier
 * @property {number} estimated_revenue
 */

/**
 * @typedef {Object} MarketContext
 * @property {number} competitor_openings
 * @property {number} competitor_avg_price
 * @property {number[]} search_volume_trend
 */

/**
 * @typedef {Object} SimulatorResult
 * @property {string} courseName
 * @property {string} field
 * @property {number} predictedCount
 * @property {'High'|'Mid'|'Low'} demandTier
 * @property {{ lower: number, upper: number }} confidenceInterval
 * @property {string} modelUsed
 * @property {string} predictionDate
 * @property {SimulatorResultMarketing|null} marketing
 * @property {SimulatorResultOperations|null} operations
 * @property {{ baseline: ScenarioItem, optimistic: ScenarioItem, pessimistic: ScenarioItem }|null} scenarios
 * @property {MarketContext|null} marketContext
 */

/**
 * @typedef {Object} StatusItem
 * @property {string} serviceName
 * @property {'ok'|'degraded'|'down'} status
 * @property {string} lastSync
 * @property {Object} metrics
 */

/**
 * @typedef {Object} RecommendationItem
 * @property {string} text
 * @property {string|null} link
 */

/**
 * @typedef {Object} LeadConversionData
 * @property {string} field
 * @property {number} estimatedConversions
 * @property {ChartPoint[]} conversionTrend
 * @property {ChartPoint[]} consultationTrend
 * @property {RecommendationItem[]} recommendations
 */

/**
 * @typedef {Object} MarketingTimingData
 * @property {string} courseName
 * @property {'High'|'Mid'|'Low'} demandTier
 * @property {number} adWeeksBefore
 * @property {number} earlybirdDays
 * @property {number} discountRate
 */

/**
 * @typedef {Object} ClosureRiskData
 * @property {number} riskScore
 * @property {'high'|'medium'|'low'} riskLevel
 * @property {string[]} contributingFactors
 * @property {string} recommendation
 * @property {null} riskTrend
 */

/**
 * @typedef {Object} ClassItem
 * @property {number} classNumber
 * @property {string} instructorSlot
 * @property {string} timeSlot
 * @property {number} capacity
 */

/**
 * @typedef {Object} ScheduleSuggestData
 * @property {string} courseName
 * @property {string} startDate
 * @property {number} predictedEnrollment
 * @property {number} instructors
 * @property {number} classrooms
 * @property {{ classes: ClassItem[], summary: Object }} assignmentPlan
 */

/**
 * @typedef {Object} AgeGroupItem
 * @property {string} group
 * @property {number} ratio
 */

/**
 * @typedef {Object} PurposeGroupItem
 * @property {string} purpose
 * @property {number} ratio
 */

/**
 * @typedef {Object} DemographicsData
 * @property {string} field
 * @property {AgeGroupItem[]} ageDistribution
 * @property {PurposeGroupItem[]} purposeDistribution
 * @property {string} trend
 */

/**
 * @typedef {Object} CompetitorData
 * @property {string} field
 * @property {number} competitorOpenings
 * @property {number|null} previousOpenings
 * @property {number} competitorAvgPrice
 * @property {number|null} previousAvgPrice
 * @property {number} saturationIndex
 * @property {string} recommendation
 */

/**
 * @typedef {Object} OptimalStartCandidate
 * @property {string} date
 * @property {number} predictedEnrollment
 * @property {'High'|'Mid'|'Low'} demandTier
 * @property {number} compositeScore
 */

/**
 * @typedef {Object} OptimalStartData
 * @property {OptimalStartCandidate[]} topCandidates
 */
