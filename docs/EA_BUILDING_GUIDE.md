# alphaQuant Framework - EA Building Guide

## Overview

This guide is designed for coding assistants helping clients build modular Expert Advisors (EAs) using the alphaQuant Framework. The framework provides a handle-based architecture with 20 specialized modules delivered as protected .ex5 libraries.

## What Clients Receive

When a client has the alphaQuant Framework, they have:

1. **Compiled Libraries (.ex5)**: Protected code in `MQL5/Libraries/` directory
   - `AlphaQuant_Logger.ex5`
   - `AlphaQuant_PositionTracker.ex5`
   - `AlphaQuant_RiskManager.ex5`
   - And 17 more module libraries...

2. **API Headers (.mqh)**: Function declarations in an `API/` folder
   - Individual module headers (e.g., `Logger_API.mqh`, `RiskManager_API.mqh`)
   - `CommonTypes.mqh` (shared enums and constants)
   - `FrameworkCore.mqh` (master include file)

3. **Template EA**: `ModularEA_Template.mq5` as a starting point

## Architecture Overview

### Handle-Based Pattern

The framework uses an object pool pattern with integer handles:
- Each module maintains an internal pool of instances
- `ModuleName_Create()` returns an integer handle (>= 0 on success, -1 on failure)
- The handle references an internal instance throughout the EA's lifetime
- `ModuleName_Destroy()` releases the instance back to the pool

### Module Structure

Each module follows this pattern:
```cpp
// In AlphaQuant_ModuleName.ex5 (compiled library)
#property library

int ModuleName_Create(...) export { /* creates instance */ }
bool ModuleName_Destroy(int handle) export { /* destroys instance */ }
// ... other exported functions
```

### API Headers

API headers use `#import` to declare library functions:
```cpp
// In ModuleName_API.mqh
#import "AlphaQuant_ModuleName.ex5"
   int  ModuleName_Create(...);
   bool ModuleName_Destroy(int handle);
   // ... other functions
#import
```

### FrameworkCore.mqh

The master include file that brings everything together:
```cpp
#include "CommonTypes.mqh"
#include "Logger_API.mqh"
#include "PositionTracker_API.mqh"
#include "RiskManager_API.mqh"
// ... all 20 module APIs
```

EAs only need one include:
```cpp
#include <Framework/FrameworkCore.mqh>
// OR
#include "..\API\FrameworkCore.mqh"
```

## ⚠️ CRITICAL: Template Workflow

### NEVER Modify the Original Template

**IMPORTANT**: The `ModularEA_Template.mq5` is your master template and should NEVER be modified directly.

**Correct Workflow**:
1. **Copy** `ModularEA_Template.mq5` to a new file
2. **Rename** with your project/strategy name (e.g., `MicroCanal_EA.mq5`, `ScalpingStrategy_EA.mq5`)
3. **Modify** only the renamed copy
4. **Preserve** the original template for future projects

**Example Directory Structure**:
```
Templates/
  ├── ModularEA_Template.mq5        ← NEVER modify (master template)
  ├── MicroCanal_EA.mq5             ← Your project 1
  ├── ScalpingStrategy_EA.mq5       ← Your project 2
  └── TrendFollowing_EA.mq5         ← Your project 3
```

**Why This Matters**:
- ✅ Template remains clean for new projects
- ✅ Easy to compare changes vs. original
- ✅ Can create multiple strategies from same base
- ✅ Framework updates don't break your EAs

---

## Quick Start Guide

### Step 1: Copy the Template

**ALWAYS start by creating a copy** of `ModularEA_Template.mq5`:

```bash
# Example: Creating "MicroCanal_EA.mq5"
copy ModularEA_Template.mq5 MicroCanal_EA.mq5
```

Then update the file header:
```cpp
//+------------------------------------------------------------------+
//|                                            MyCustomStrategy.mq5 |
//+------------------------------------------------------------------+
#property copyright "Your Name"
#property version   "1.00"
#property strict

#include <Framework/FrameworkCore.mqh>
```

### Step 2: Define Input Parameters

Customize inputs for your strategy:
```cpp
input group "=== Strategy Settings ==="
input ENUM_TRIGGER_TYPE InpTriggerType = TRIGGER_TIME_BASED;
input int InpStartHour = 9;
input int InpStartMinute = 30;

input group "=== Risk Management ==="
input ENUM_RISK_TYPE InpRiskType = RISK_FIXED_LOTS;
input double InpFixedLots = 0.1;
```

### Step 3: Declare Module Handles

```cpp
// Global handles
int g_hLogger = -1;
int g_hLicense = -1;
int g_hRiskManager = -1;
int g_hStopLoss = -1;
int g_hTakeProfit = -1;
int g_hOrderManager = -1;
// ... other handles as needed
```

### Step 4: Initialize Modules in OnInit

Follow the dependency order:
```cpp
int OnInit()
{
   // 1. Logger (no dependencies)
   g_hLogger = Logger_Create("MyEA", LOG_LEVEL_INFO, LOG_OUTPUT_TERMINAL, true);
   if(g_hLogger < 0) return INIT_FAILED;

   // 2. License check
   g_hLicense = License_Create(g_hLogger);
   if(g_hLicense < 0) return INIT_FAILED;
   if(!License_IsAuthorized(g_hLicense))
   {
      Logger_Error(g_hLogger, "License validation failed");
      return INIT_FAILED;
   }

   // 3. Create other modules...
   g_hRiskManager = RiskManager_Create(_Symbol, MAGIC_NUMBER, g_hLogger,
                                       InpRiskType, InpFixedLots,
                                       InpInitialAllocation, InpRiskPercent,
                                       CUSTOMER_PROFILE_CONSERVATIVE);
   if(g_hRiskManager < 0) return INIT_FAILED;

   return INIT_SUCCEEDED;
}
```

### Step 5: Implement Trading Logic in OnTick

```cpp
void OnTick()
{
   // Check for new bar
   if(IsNewBar())
   {
      // Generate signals
      int signal = GenerateSignal();

      if(signal == SIGNAL_BUY || signal == SIGNAL_SELL)
      {
         ExecuteTrade(signal);
      }
   }

   // Process trailing stops
   TrailingStop_ProcessTrailingStops(g_hTrailingStop);

   // Monitor OCO pairs
   OCO_MonitorOCOPairs(g_hOCO);
}
```

### Step 6: Clean Up in OnDeinit

Destroy handles in REVERSE order of creation:
```cpp
void OnDeinit(const int reason)
{
   // Destroy in reverse order
   if(g_hOrderManager >= 0) OrderManager_Destroy(g_hOrderManager);
   if(g_hTrailingStop >= 0) TrailingStop_Destroy(g_hTrailingStop);
   if(g_hRiskManager >= 0) RiskManager_Destroy(g_hRiskManager);
   if(g_hLicense >= 0) License_Destroy(g_hLicense);
   if(g_hLogger >= 0) Logger_Destroy(g_hLogger);
}
```

## Complete Module Catalog

### Module 1: Logger (TYPE_ID = 1)

**Purpose**: Centralized logging system with multiple output channels and log levels.

**Functions**:
```cpp
int Logger_Create(
   const string prefix,      // Prefix for all log messages
   int level = 3,           // Log level (0=NONE, 1=ERROR, 2=WARNING, 3=INFO, 4=DEBUG, 5=VERBOSE)
   int output = 1,          // Output channel (1=TERMINAL, 2=FILE, 3=BOTH)
   bool timestamp = true    // Include timestamp in messages
);

bool Logger_Destroy(int handle);

void Logger_Info(int handle, const string message);      // Log informational message
void Logger_Error(int handle, const string message);     // Log error message
void Logger_Warning(int handle, const string message);   // Log warning message
void Logger_Debug(int handle, const string message);     // Log debug message
void Logger_Verbose(int handle, const string message);   // Log verbose message
void Logger_LogHeader(int handle, const string header);  // Log formatted header
```

**Usage Example**:
```cpp
int hLogger = Logger_Create("MyEA", LOG_LEVEL_INFO, LOG_OUTPUT_TERMINAL, true);
if(hLogger >= 0)
{
   Logger_Info(hLogger, "EA initialized successfully");
   Logger_Warning(hLogger, "High spread detected: " + DoubleToString(spread, 1));
   Logger_Error(hLogger, "Failed to open position: " + IntegerToString(GetLastError()));
}
```

---

### Module 2: PositionTracker (TYPE_ID = 2)

**Purpose**: Tracks open positions, manages position lifecycle, and provides recovery after EA restart.

**Functions**:
```cpp
int PositionTracker_Create(
   const string symbol,      // Trading symbol
   long magic,              // Magic number
   int loggerHandle         // Logger handle for logging
);

bool PositionTracker_Destroy(int handle);

void PositionTracker_RegisterPositionOpened(
   int handle,
   ulong positionId,        // Unique position ID
   ulong ticket            // MT5 position ticket
);

void PositionTracker_RegisterPositionClosed(int handle, ulong positionId);

bool PositionTracker_IsPositionOpen(int handle, ulong positionId);

bool PositionTracker_RecoverStateAfterRestart(int handle);  // Recover positions after restart

void PositionTracker_SyncWithMT5Positions(int handle);      // Sync with MT5 positions

int  PositionTracker_GetOpenCount(int handle);              // Get count of open positions
int  PositionTracker_GetTotalCount(int handle);             // Get total positions tracked

string PositionTracker_GetDebugInfo(int handle);            // Get debug information
bool   PositionTracker_IsInitialized(int handle);           // Check initialization status
int    PositionTracker_GetPoolUsage();                      // Get pool usage statistics

void PositionTracker_UpdatePositionSL(
   int handle,
   ulong positionId,
   double newSL             // New stop loss level
);
```

**Usage Example**:
```cpp
int hTracker = PositionTracker_Create(_Symbol, MAGIC_NUMBER, hLogger);
if(hTracker >= 0)
{
   // After opening a position
   PositionTracker_RegisterPositionOpened(hTracker, uniqueID, ticket);

   // Check if position is still open
   if(PositionTracker_IsPositionOpen(hTracker, uniqueID))
   {
      // Position is active
   }

   // After EA restart
   PositionTracker_RecoverStateAfterRestart(hTracker);
}
```

---

### Module 3: RiskManager (TYPE_ID = 3)

**Purpose**: Comprehensive risk management including lot sizing, progression systems, and drawdown control.

**Functions**:
```cpp
int RiskManager_Create(
   const string symbol,
   long magic,
   int loggerHandle,
   int riskType,            // RISK_FIXED_LOTS, RISK_PERCENTAGE, RISK_FIXED_ALLOCATION
   double fixedLots,        // Fixed lot size (if RISK_FIXED_LOTS)
   double initialAllocation, // Initial capital allocation
   double riskPercentage,   // Risk percentage per trade
   int customerProfile      // CUSTOMER_PROFILE_CONSERVATIVE/MODERATE/AGGRESSIVE
);

bool RiskManager_Destroy(int handle);

// Progression Configuration
bool RiskManager_SetProgression(
   int handle,
   bool enable,             // Enable progression
   double percent,          // Progression percentage per level
   int maxLevel,           // Maximum progression level
   int resetWins,          // Consecutive wins to reset
   int resetLosses         // Consecutive losses to reset
);

bool RiskManager_SetProgressionLimits(
   int handle,
   double maxR,            // Maximum risk value
   double maxLots          // Maximum lot size
);

// Lot Limits
bool RiskManager_SetLotLimits(
   int handle,
   double maxLot,          // Maximum lot size
   double minLot,          // Minimum lot size
   double maxRiskPercent   // Maximum risk percentage
);

// Drawdown Limits
bool RiskManager_SetDrawdownLimits(
   int handle,
   double maxPercent,      // Maximum drawdown percentage
   double maxAbsolute      // Maximum absolute drawdown
);

// Testing
bool RiskManager_SetTestMode(
   int handle,
   bool testMode,          // Enable test mode
   bool verboseLogging     // Enable verbose logging
);

// Lot Calculation
double RiskManager_CalculateLotSize(
   int handle,
   double entryPrice,
   double stopPrice        // Stop loss price
);

double RiskManager_CalculateLotForR(
   int handle,
   double riskValue,       // Specific risk value (R)
   double entryPrice,
   double stopPrice
);

// Operation Callbacks (MUST BE CALLED)
void RiskManager_OnOperationResult(
   int handle,
   bool isWin,            // True if trade was profitable
   double profit          // Profit/loss amount
);

void RiskManager_OnNewOperation(int handle);  // Call before opening new position
void RiskManager_OnNewDay(int handle);        // Call on new trading day
void RiskManager_Reset(int handle);           // Reset progression state

// Getters
double RiskManager_GetCurrentLotSize(int handle);
int    RiskManager_GetProgressionLevel(int handle);
bool   RiskManager_IsInProgression(int handle);
int    RiskManager_GetConsecutiveWins(int handle);
int    RiskManager_GetConsecutiveLosses(int handle);
double RiskManager_GetCurrentAllocation(int handle);
double RiskManager_GetCurrentRisk(int handle);
double RiskManager_GetTotalProfitLoss(int handle);
double RiskManager_GetCurrentDrawdown(int handle);
double RiskManager_GetMaxDrawdown(int handle);
double RiskManager_GetRiskPercentage(int handle);
bool   RiskManager_CanOperate(int handle);  // Check if trading is allowed

// Reports
string RiskManager_GetProgressionReport(int handle);
string RiskManager_GetRiskReport(int handle);

// Persistence
bool RiskManager_SaveStateToFile(int handle);
bool RiskManager_LoadStateFromFile(int handle);

// Status
bool RiskManager_IsInitialized(int handle);
int  RiskManager_GetPoolUsage();
```

**Usage Example**:
```cpp
// Create risk manager
int hRisk = RiskManager_Create(_Symbol, MAGIC_NUMBER, hLogger,
                               RISK_PERCENTAGE, 0.0, 10000.0, 2.0,
                               CUSTOMER_PROFILE_MODERATE);

// Configure progression
RiskManager_SetProgression(hRisk, true, 50.0, 3, 2, 2);
RiskManager_SetProgressionLimits(hRisk, 500.0, 1.0);

// Calculate lot size
double entryPrice = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
double stopLoss = entryPrice - 50 * _Point;
double lotSize = RiskManager_CalculateLotSize(hRisk, entryPrice, stopLoss);

// Check if can operate
if(RiskManager_CanOperate(hRisk))
{
   RiskManager_OnNewOperation(hRisk);
   // Execute trade...

   // After trade closes
   RiskManager_OnOperationResult(hRisk, profit > 0, profit);
}

// Daily maintenance
if(IsNewDay())
{
   RiskManager_OnNewDay(hRisk);
}
```

---

### Module 4: StopLossManager (TYPE_ID = 4)

**Purpose**: Calculates stop loss levels using various methods (ATR, fixed points, graphic levels).

**Functions**:
```cpp
int StopLoss_Create(
   const string symbol,
   int timeframe,
   int loggerHandle,
   int slType,              // STOP_LOSS_ATR, STOP_LOSS_FIXED, STOP_LOSS_GRAPHIC
   int atrPeriod,          // ATR period (for ATR type)
   double atrMultiplier,   // ATR multiplier
   int fixedPoints,        // Fixed points (for FIXED type)
   int graphicBufferTicks, // Buffer ticks for graphic levels
   int minStopPoints,      // Minimum stop distance in points
   int maxStopPoints       // Maximum stop distance in points
);

bool StopLoss_Destroy(int handle);

double StopLoss_CalculateStopLoss(
   int handle,
   int signalType,         // SIGNAL_BUY or SIGNAL_SELL
   double entryPrice,
   datetime triggerBarTime // Bar time for graphic levels
);

double StopLoss_GetMinimumStopLevel(int handle);

bool StopLoss_IsStopLevelValid(
   int handle,
   double stopLoss,
   double entryPrice,
   int signalType
);

int  StopLoss_GetTotalCalculations(int handle);
bool StopLoss_IsInitialized(int handle);
int  StopLoss_GetPoolUsage();
```

**Usage Example**:
```cpp
// Create SL manager with ATR-based stops
int hSL = StopLoss_Create(_Symbol, PERIOD_CURRENT, hLogger,
                          STOP_LOSS_ATR, 14, 2.0, 0, 0, 20, 200);

// Calculate stop loss
double entryPrice = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
double stopLoss = StopLoss_CalculateStopLoss(hSL, SIGNAL_BUY, entryPrice, iTime(_Symbol, PERIOD_CURRENT, 1));

// Validate stop level
if(StopLoss_IsStopLevelValid(hSL, stopLoss, entryPrice, SIGNAL_BUY))
{
   // Stop loss is valid
}
```

---

### Module 5: TakeProfitManager (TYPE_ID = 5)

**Purpose**: Calculates take profit levels using various methods (fixed, risk-reward, ZigZag, ATR).

**Functions**:
```cpp
int TakeProfit_Create(
   const string symbol,
   int timeframe,
   int loggerHandle,
   int tpType,             // TP_FIXED, TP_RISK_REWARD, TP_ZIGZAG, TP_ATR
   int fixedPoints,        // Fixed points (for TP_FIXED)
   double rrMultiplier,    // Risk-reward ratio (for TP_RISK_REWARD)
   int zigzagDepth,        // ZigZag parameters
   int zigzagDeviation,
   int zigzagBackstep,
   int zigzagBufferTicks,  // Buffer ticks for ZigZag
   int minTPPoints,        // Minimum TP distance
   int maxTPPoints,        // Maximum TP distance
   int atrTPPeriod,        // ATR period (for TP_ATR)
   double atrTPPercent,    // ATR percentage
   int atrTPTimeframe      // ATR timeframe
);

bool TakeProfit_Destroy(int handle);

double TakeProfit_Calculate(
   int handle,
   int signalType,         // SIGNAL_BUY or SIGNAL_SELL
   double entryPrice,
   double stopLoss         // Required for TP_RISK_REWARD
);

bool TakeProfit_IsValid(
   int handle,
   double takeProfit,
   double entryPrice,
   int signalType
);

double TakeProfit_GetMinimumLevel(int handle);
int    TakeProfit_GetTotalCalculations(int handle);
bool   TakeProfit_IsInitialized(int handle);
int    TakeProfit_GetPoolUsage();
```

**Usage Example**:
```cpp
// Create TP manager with risk-reward ratio
int hTP = TakeProfit_Create(_Symbol, PERIOD_CURRENT, hLogger,
                            TP_RISK_REWARD, 0, 2.0,
                            0, 0, 0, 0, 50, 500, 0, 0.0, 0);

// Calculate take profit
double takeProfit = TakeProfit_Calculate(hTP, SIGNAL_BUY, entryPrice, stopLoss);

// Validate TP level
if(TakeProfit_IsValid(hTP, takeProfit, entryPrice, SIGNAL_BUY))
{
   // Take profit is valid
}
```

---

### Module 6: OCOSystem (TYPE_ID = 6)

**Purpose**: Manages One-Cancels-Other (OCO) order pairs for take profit and stop loss.

**Functions**:
```cpp
int OCO_Create(
   const string symbol,
   int loggerHandle,
   long magic,
   int maxPairs,           // Maximum concurrent OCO pairs
   int maxHistory,         // Maximum history to keep
   bool enableRecovery     // Enable recovery after restart
);

bool OCO_Destroy(int handle);

int OCO_CreateOCOPair(
   int handle,
   ulong positionTicket,   // Position ticket
   double volume,          // Order volume
   double tpPrice,         // Take profit price
   double slPrice          // Stop loss price
);

bool OCO_CancelOCOPair(int handle, int uniqueId);

bool OCO_CancelByPosition(int handle, ulong positionTicket);

void OCO_MonitorOCOPairs(int handle);  // MUST BE CALLED ON EVERY TICK

void OCO_OnOrderExecution(
   int handle,
   ulong ticket,
   double executedVolume
);

void OCO_OnPositionClose(int handle, ulong positionTicket);

int  OCO_GetActivePairCount(int handle);
int  OCO_GetTotalPairCount(int handle);
bool OCO_HasActivePairForPosition(int handle, ulong positionTicket);

string OCO_GetDebugInfo(int handle);
bool   OCO_IsInitialized(int handle);
int    OCO_GetPoolUsage();
```

**Usage Example**:
```cpp
int hOCO = OCO_Create(_Symbol, hLogger, MAGIC_NUMBER, 20, 100, true);

// After opening a position
int ocoId = OCO_CreateOCOPair(hOCO, posTicket, volume, tpPrice, slPrice);

// On every tick
void OnTick()
{
   OCO_MonitorOCOPairs(hOCO);  // Essential for OCO functionality
}

// Cancel OCO when position closes
OCO_OnPositionClose(hOCO, posTicket);
```

---

### Module 7: PostExecutionManager (TYPE_ID = 7)

**Purpose**: Adjusts stop loss levels after position opens based on market structure.

**Functions**:
```cpp
int PostExec_Create(
   const string symbol,
   int timeframe,
   int loggerHandle,
   bool enableAdjustment,  // Enable post-execution adjustment
   int maxAdjustments,     // Maximum adjustments per position
   int checkDelayBars      // Bars to wait before checking
);

bool PostExec_Destroy(int handle);

double PostExec_CheckAndAdjustInitialStop(
   int handle,
   ulong positionTicket,
   int signalType,
   datetime triggerBarTime,
   double currentStopLoss  // Returns adjusted SL or original
);

int    PostExec_GetAdjustmentCount(int handle);
string PostExec_GetStatistics(int handle);
bool   PostExec_IsInitialized(int handle);
int    PostExec_GetPoolUsage();
```

**Usage Example**:
```cpp
int hPostExec = PostExec_Create(_Symbol, PERIOD_CURRENT, hLogger, true, 2, 1);

// After opening position (call after delay bars)
double adjustedSL = PostExec_CheckAndAdjustInitialStop(hPostExec,
                                                       ticket,
                                                       SIGNAL_BUY,
                                                       triggerTime,
                                                       currentSL);
if(adjustedSL != currentSL)
{
   // Modify position with new SL
}
```

---

### Module 8: TrailingStopManager (TYPE_ID = 8)

**Purpose**: Implements various trailing stop strategies (breakeven, fixed step, ATR-based).

**Functions**:
```cpp
int TrailingStop_Create(
   const string symbol,
   int timeframe,
   int loggerHandle,
   int posTrackerHandle,   // PositionTracker handle (dependency)
   int trailingType,       // TRAILING_STOP_FIXED, TRAILING_STOP_ATR
   int activationMode,     // TRAILING_ACTIVATION_IMMEDIATE, TRAILING_ACTIVATION_RR
   int priceSource,        // PRICE_SOURCE_BID_ASK, PRICE_SOURCE_CLOSE
   double rrBreakeven,     // RR ratio for breakeven
   double rrTrailing,      // RR ratio for trailing activation
   int trailingStepPoints, // Trailing step in points
   bool onlyFavorableBars, // Only trail on favorable bar close
   int bufferTicks,        // Buffer ticks
   int atrPeriod,          // ATR period (for ATR type)
   double atrBreakevenMultiplier,
   double atrMultiplier,
   int minTrailPoints,
   double minProfitForActivation
);

bool TrailingStop_Destroy(int handle);

void TrailingStop_ProcessTrailingStops(int handle);  // MUST BE CALLED ON EVERY TICK

void TrailingStop_ActivateForPosition(int handle, ulong ticket);
void TrailingStop_DeactivateForPosition(int handle, ulong ticket);

bool TrailingStop_IsTrailingActive(int handle, ulong ticket);

int  TrailingStop_GetTotalUpdates(int handle);
int  TrailingStop_GetBreakEvenMoves(int handle);
int  TrailingStop_GetActivationsCount(int handle);
bool TrailingStop_IsInitialized(int handle);
int  TrailingStop_GetPoolUsage();
```

**Usage Example**:
```cpp
int hTrailing = TrailingStop_Create(_Symbol, PERIOD_CURRENT, hLogger, hTracker,
                                    TRAILING_STOP_FIXED,
                                    TRAILING_ACTIVATION_RR,
                                    PRICE_SOURCE_BID_ASK,
                                    1.0, 1.5, 10, false, 2, 14, 1.0, 1.5, 10, 0.0);

// On every tick
void OnTick()
{
   TrailingStop_ProcessTrailingStops(hTrailing);
}

// After opening position
TrailingStop_ActivateForPosition(hTrailing, ticket);
```

---

### Module 9: TriggerMonitor (TYPE_ID = 9)

**Purpose**: Internal module for monitoring pending order triggers. Not typically used directly in EA code.

---

### Module 10: OrderManager (TYPE_ID = 10)

**Purpose**: Executes and manages all order operations (market, pending, modifications, closures).

**Functions**:
```cpp
int OrderManager_Create(
   const string symbol,
   int magic,
   int loggerHandle,
   int ocoHandle,          // OCOSystem handle (0 if not using OCO)
   int triggerHandle,      // TriggerMonitor handle (0 if not using)
   int slippage,           // Maximum slippage in points
   bool useOCO,           // Use OCO for TP/SL
   double riskRewardRatio  // Risk-reward ratio for OCO
);

bool OrderManager_Destroy(int handle);

// Market Orders
ulong OrderManager_ExecuteMarketOrder(
   int handle,
   int signalType,         // SIGNAL_BUY or SIGNAL_SELL
   double volume,
   double price,           // Reference price (can be 0 for current)
   double sl,
   double tp,
   const string comment
);

// Pending Orders
ulong OrderManager_PlacePendingOrder(
   int handle,
   int signalType,         // SIGNAL_BUY_STOP, SIGNAL_SELL_STOP, etc.
   double volume,
   double price,           // Pending order price
   double pendingDistance, // Distance from current price
   double sl,
   double tp,
   datetime expiration,
   const string comment
);

// Order Modifications
bool OrderManager_ModifyOrder(
   int handle,
   ulong ticket,
   double newPrice,        // New pending price (0 = no change)
   double newSL,          // New SL (0 = no change)
   double newTP           // New TP (0 = no change)
);

bool OrderManager_CancelOrder(int handle, ulong ticket);

// Position Closing
bool OrderManager_ClosePosition(int handle, ulong ticket);
bool OrderManager_CloseAllPositions(int handle);
bool OrderManager_ClosePositionsInProfit(int handle);
bool OrderManager_ClosePositionsWithMinProfitTicks(int handle, int minProfitTicks);

// Last Operation Info
ulong  OrderManager_GetLastTicket(int handle);
int    OrderManager_GetLastError(int handle);
string OrderManager_GetLastErrorDescription(int handle);
bool   OrderManager_WasLastSuccessful(int handle);
double OrderManager_GetLastExecutedPrice(int handle);
double OrderManager_GetLastExecutedVolume(int handle);

// Configuration
bool OrderManager_SetMaxRetries(int handle, int retries);
bool OrderManager_SetRetryDelay(int handle, int delay);
bool OrderManager_SetSpreadValidation(int handle, bool validate, double maxSpread);

// Statistics
int    OrderManager_GetTotalOrders(int handle);
int    OrderManager_GetSuccessfulOrders(int handle);
int    OrderManager_GetFailedOrders(int handle);
double OrderManager_GetSuccessRate(int handle);

// Status
bool OrderManager_IsInitialized(int handle);
int  OrderManager_GetPoolUsage();
```

**Usage Example**:
```cpp
int hOrder = OrderManager_Create(_Symbol, MAGIC_NUMBER, hLogger, hOCO, 0, 10, true, 2.0);

// Execute market order
ulong ticket = OrderManager_ExecuteMarketOrder(hOrder, SIGNAL_BUY, lotSize, 0, slPrice, tpPrice, "Buy signal");

if(OrderManager_WasLastSuccessful(hOrder))
{
   Logger_Info(hLogger, "Order executed: " + IntegerToString(ticket));
}
else
{
   Logger_Error(hLogger, "Order failed: " + OrderManager_GetLastErrorDescription(hOrder));
}

// Place pending order
ulong pendingTicket = OrderManager_PlacePendingOrder(hOrder, SIGNAL_BUY_STOP,
                                                     lotSize, pendingPrice, 20,
                                                     slPrice, tpPrice, 0, "Buy Stop");

// Modify position SL
OrderManager_ModifyOrder(hOrder, ticket, 0, newSL, 0);

// Close all profitable positions
OrderManager_ClosePositionsInProfit(hOrder);
```

---

### Module 11: MovingAverageSlope (TYPE_ID = 11)

**Purpose**: Internal module used by TrendDetector for slope calculations. Not typically used directly in EA code.

---

### Module 12: ZigZagReader (TYPE_ID = 12)

**Purpose**: Internal module used by other modules for ZigZag analysis. Not typically used directly in EA code.

---

### Module 13: MultiIndicatorAnalyzer (TYPE_ID = 13)

**Purpose**: Analyzes multiple indicators (Stochastic, RSI, ZigZag) for confirmation and filtering.

**Functions**:
```cpp
int MultiInd_Create(
   const string symbol,
   int timeframe,
   int loggerHandle,
   int stochK,             // Stochastic %K period
   int stochD,             // Stochastic %D period
   int stochSlowing,       // Stochastic slowing
   int stochMethod,        // MA method for Stochastic
   int stochPriceField,    // Price field (0=Low/High, 1=Close/Close)
   double stochOversold,   // Oversold level (e.g., 20)
   double stochOverbought, // Overbought level (e.g., 80)
   int rsiPeriod,          // RSI period
   int rsiAppliedPrice,    // RSI applied price
   double rsiOversold,     // RSI oversold level (e.g., 30)
   double rsiOverbought,   // RSI overbought level (e.g., 70)
   int zigzagDepth,        // ZigZag parameters
   int zigzagDeviation,
   int zigzagBackstep
);

bool MultiInd_Destroy(int handle);

bool MultiInd_RefreshData(int handle);  // Refresh indicator data

// Stochastic
bool MultiInd_IsStochasticOversold(int handle, int shift);
bool MultiInd_IsStochasticOverbought(int handle, int shift);
double MultiInd_GetStochasticMain(int handle, int shift);
double MultiInd_GetStochasticSignal(int handle, int shift);

// RSI
bool MultiInd_IsRSIOversold(int handle, int shift);
bool MultiInd_IsRSIOverbought(int handle, int shift);
double MultiInd_GetRSIValue(int handle, int shift);

// Combined Conditions
bool MultiInd_AreOversoldConditionsMet(int handle, int shift);   // Both RSI and Stoch oversold
bool MultiInd_AreOverboughtConditionsMet(int handle, int shift); // Both RSI and Stoch overbought

// Indicator Handles (for advanced usage)
int MultiInd_GetStochHandle(int handle);
int MultiInd_GetRSIHandle(int handle);
int MultiInd_GetZigZagHandle(int handle);

// Status
bool MultiInd_IsInitialized(int handle);
int  MultiInd_GetPoolUsage();
```

**Usage Example**:
```cpp
int hMultiInd = MultiInd_Create(_Symbol, PERIOD_CURRENT, hLogger,
                                14, 3, 3, MODE_SMA, 0, 20.0, 80.0,
                                14, PRICE_CLOSE, 30.0, 70.0,
                                12, 5, 3);

// Use as signal filter
int signal = GenerateSignal();

MultiInd_RefreshData(hMultiInd);

if(signal == SIGNAL_BUY)
{
   // Confirm with oversold conditions
   if(MultiInd_AreOversoldConditionsMet(hMultiInd, 1))
   {
      // Execute buy trade
   }
}
else if(signal == SIGNAL_SELL)
{
   // Confirm with overbought conditions
   if(MultiInd_AreOverboughtConditionsMet(hMultiInd, 1))
   {
      // Execute sell trade
   }
}

// Or check individual indicators
if(MultiInd_IsRSIOversold(hMultiInd, 1))
{
   double rsiValue = MultiInd_GetRSIValue(hMultiInd, 1);
   Logger_Info(hLogger, "RSI oversold: " + DoubleToString(rsiValue, 2));
}
```

---

### Module 14: TriggerSystem (TYPE_ID = 14)

**Purpose**: Generates trading signals based on time, price action, and breakout patterns.

**Functions**:
```cpp
int Trigger_Create(
   const string symbol,
   int timeframe,
   int loggerHandle,
   int triggerType,        // TRIGGER_TIME_BASED, TRIGGER_BREAKOUT, etc.
   bool useFirstBarOfDay,  // Use first bar of day as reference
   int refCandleHour,      // Reference candle hour
   int refCandleMin,       // Reference candle minute
   int refCandleToleranceMinutes, // Tolerance for ref candle
   int startHour,          // Trading start hour
   int startMinute,        // Trading start minute
   int waitingTrigger,     // Minutes to wait for trigger
   int breakoutType,       // BREAKOUT_HIGH_LOW, BREAKOUT_CLOSE, etc.
   int zigzagDepth,        // ZigZag parameters (for ZigZag breakouts)
   int zigzagDeviation,
   int zigzagBackstep
);

bool Trigger_Destroy(int handle);

int Trigger_CheckTrigger(int handle);  // Returns SIGNAL_BUY, SIGNAL_SELL, or SIGNAL_NONE

void Trigger_OnNewBar(int handle);     // Call on new bar
void Trigger_OnTick(int handle);       // Call on tick (for intrabar triggers)
void Trigger_Reset(int handle);        // Reset trigger state

// Last Trigger Info
double   Trigger_GetLastEntryPrice(int handle);
double   Trigger_GetLastConfidence(int handle);
string   Trigger_GetLastReason(int handle);
datetime Trigger_GetLastTriggerTime(int handle);
double   Trigger_GetLastTriggerHigh(int handle);
double   Trigger_GetLastTriggerLow(int handle);

// Status
string Trigger_GetStatus(int handle);
string Trigger_GetTriggerName(int handle);
bool   Trigger_IsInitialized(int handle);
int    Trigger_GetPoolUsage();
```

**Usage Example**:
```cpp
// Time-based trigger (trade after 9:30 AM breakout)
int hTrigger = Trigger_Create(_Symbol, PERIOD_M5, hLogger,
                              TRIGGER_TIME_BASED,
                              true, 9, 30, 5,
                              9, 30, 30,
                              BREAKOUT_HIGH_LOW,
                              0, 0, 0);

void OnTick()
{
   static datetime lastBar = 0;
   datetime currentBar = iTime(_Symbol, PERIOD_CURRENT, 0);

   if(currentBar != lastBar)
   {
      lastBar = currentBar;
      Trigger_OnNewBar(hTrigger);

      int signal = Trigger_CheckTrigger(hTrigger);

      if(signal == SIGNAL_BUY || signal == SIGNAL_SELL)
      {
         double entryPrice = Trigger_GetLastEntryPrice(hTrigger);
         string reason = Trigger_GetLastReason(hTrigger);

         Logger_Info(hLogger, "Trigger fired: " + reason);
         ExecuteTrade(signal, entryPrice);
      }
   }
}
```

---

### Module 15: BookAnalysis (TYPE_ID = 15)

**Purpose**: Analyzes market depth (DOM) for order flow, pressure, and aggression signals.

**Functions**:
```cpp
int Book_Create(
   string symbol,
   int maxLevels,          // Maximum DOM levels to analyze
   int loggerHandle,
   bool enableDebugLog
);

void Book_Destroy(int handle);

bool Book_Subscribe(int handle);    // Subscribe to DOM updates
bool Book_Unsubscribe(int handle);  // Unsubscribe from DOM

bool Book_ReadAndAnalyze(int handle);  // Read and analyze current DOM

void Book_OnBookUpdate(int handle);    // Call from OnBookEvent()

// Configuration
void Book_SetPressureConfig(
   int handle,
   int method,             // PRESSURE_SIMPLE, PRESSURE_WEIGHTED, PRESSURE_EXPONENTIAL
   int weight,             // WEIGHT_UNIFORM, WEIGHT_LINEAR, WEIGHT_EXPONENTIAL
   int maxLvls,           // Max levels for calculation
   double decay,          // Decay factor for exponential weighting
   double bullThresh,     // Bullish threshold
   double bearThresh      // Bearish threshold
);

void Book_SetAggressionConfig(
   int handle,
   double threshold,      // Aggression threshold
   double neutralZone     // Neutral zone
);

// Status
int Book_GetStatus(int handle);      // Returns ENUM_BOOK_STATUS
int Book_GetLevels(int handle);      // Number of DOM levels

// Price Data
double Book_GetBidPrice(int handle);
double Book_GetAskPrice(int handle);

// Pressure Analysis
double Book_GetBuyPressurePct(int handle);   // Buy pressure percentage
double Book_GetSellPressurePct(int handle);  // Sell pressure percentage
double Book_GetPressureRatio(int handle);    // Buy/Sell ratio
double Book_GetPressureImbalance(int handle); // Imbalance metric
int    Book_GetPressureSignal(int handle);   // SIGNAL_BUY/SELL/NONE
double Book_GetPressureStrength(int handle); // Signal strength

// Aggression Analysis
double Book_GetNetAggression(int handle);    // Net aggression
double Book_GetAggressionRatio(int handle);  // Aggression ratio
int    Book_GetAggressionSignal(int handle); // SIGNAL_BUY/SELL/NONE

// Reports
string Book_GetSummary(int handle);
bool   Book_IsInitialized(int handle);
```

**Usage Example**:
```cpp
int hBook = Book_Create(_Symbol, 10, hLogger, false);

if(Book_Subscribe(hBook))
{
   Book_SetPressureConfig(hBook, PRESSURE_WEIGHTED, WEIGHT_LINEAR,
                          10, 0.8, 0.6, 0.6);
   Book_SetAggressionConfig(hBook, 0.3, 0.1);
}

void OnBookEvent(const string &symbol)
{
   if(symbol == _Symbol)
   {
      Book_OnBookUpdate(hBook);

      if(Book_ReadAndAnalyze(hBook))
      {
         int pressureSignal = Book_GetPressureSignal(hBook);
         int aggressionSignal = Book_GetAggressionSignal(hBook);

         // Use as signal filter
         if(pressureSignal == SIGNAL_BUY && aggressionSignal == SIGNAL_BUY)
         {
            // Strong buy signal from order flow
         }
      }
   }
}
```

---

### Module 16: TimeAndSalesReader (TYPE_ID = 16)

**Purpose**: Specialized module for reading time & sales tape (tick data) for aggression analysis. Advanced usage.

---

### Module 17: DataExport (TYPE_ID = 17)

**Purpose**: Exports data to CSV files for analysis and reporting.

**Functions**:
```cpp
int Export_Create(int loggerHandle);

void Export_Destroy(int handle);

bool Export_Open(
   int handle,
   string filename,        // File name (in MQL5/Files/)
   bool append            // Append to existing file
);

void Export_Close(int handle);

void Export_SetDelimiter(int handle, string delim);  // Set CSV delimiter (default: ",")

bool Export_WriteHeader(int handle, string headerCSV);  // Write CSV header

bool Export_WriteLine(int handle, string valuesCSV);    // Write CSV line

bool Export_Flush(int handle);  // Flush buffer to disk

bool Export_InitAggressionFile(
   int handle,
   string symbol,
   int timeframe,
   string customName
);
```

**Usage Example**:
```cpp
int hExport = Export_Create(hLogger);

// Open file for writing
if(Export_Open(hExport, "trade_results.csv", false))
{
   Export_WriteHeader(hExport, "Time,Signal,Entry,SL,TP,Profit");

   // Write trade data
   string line = TimeToString(TimeCurrent()) + "," +
                 IntegerToString(signal) + "," +
                 DoubleToString(entryPrice, _Digits) + "," +
                 DoubleToString(slPrice, _Digits) + "," +
                 DoubleToString(tpPrice, _Digits) + "," +
                 DoubleToString(profit, 2);

   Export_WriteLine(hExport, line);
   Export_Flush(hExport);
   Export_Close(hExport);
}
```

---

### Module 18: TrendDetector (TYPE_ID = 18)

**Purpose**: Detects trend direction and strength using moving averages and slope analysis.

**Functions**:
```cpp
int Trend_Create(
   const string symbol,
   int timeframe,
   int loggerHandle,
   int maPeriod,           // MA period
   int maMethod,           // MA method (MODE_SMA, MODE_EMA, etc.)
   int maShift,            // MA shift
   int appliedPrice,       // Applied price (PRICE_CLOSE, etc.)
   double factorDecay,     // Decay factor for slope calculation
   double minSlope,        // Minimum slope for trend
   double slopeThreshold,  // Slope threshold for strength
   int confirmationCandles, // Candles required for confirmation
   bool requireConsistency  // Require consistent direction
);

bool Trend_Destroy(int handle);

bool Trend_Analyze(int handle);  // Perform trend analysis

// Trend Information
int  Trend_GetDirection(int handle);     // TREND_UP, TREND_DOWN, TREND_NEUTRAL
int  Trend_GetStrength(int handle);      // TREND_WEAK, TREND_MODERATE, TREND_STRONG
double Trend_GetSlopeValue(int handle);  // Current slope value
double Trend_GetMAValue(int handle);     // Current MA value
bool Trend_IsConfirmed(int handle);      // Is trend confirmed?

// History
datetime Trend_GetDetectionTime(int handle);
int  Trend_GetPreviousDirection(int handle, int barsBack);
bool Trend_HasDirectionChanged(int handle);

// Configuration Update
bool Trend_UpdateParams(
   int handle,
   int maPeriod,
   int maMethod,
   int maShift,
   int appliedPrice,
   double factorDecay,
   double minSlope,
   double slopeThreshold,
   int confirmationCandles,
   bool requireConsistency
);

// Reports
string Trend_GetReport(int handle);
bool   Trend_IsInitialized(int handle);
```

**Usage Example**:
```cpp
// Create trend detector with 50 EMA
int hTrend = Trend_Create(_Symbol, PERIOD_CURRENT, hLogger,
                          50, MODE_EMA, 0, PRICE_CLOSE,
                          0.9, 0.0001, 0.0003, 3, true);

void OnTick()
{
   if(IsNewBar())
   {
      if(Trend_Analyze(hTrend))
      {
         int direction = Trend_GetDirection(hTrend);
         int strength = Trend_GetStrength(hTrend);

         // Only trade with confirmed strong trends
         if(Trend_IsConfirmed(hTrend) && strength == TREND_STRONG)
         {
            if(direction == TREND_UP)
            {
               // Look for buy signals
            }
            else if(direction == TREND_DOWN)
            {
               // Look for sell signals
            }
         }

         Logger_Info(hLogger, Trend_GetReport(hTrend));
      }
   }
}
```

---

### Module 19: CandleColorizer (TYPE_ID = 19)

**Purpose**: Colors candles on the chart to visualize signals and market conditions.

**Functions**:
```cpp
int Colorizer_Create(
   const string symbol,
   int timeframe,
   int loggerHandle,
   color buyColor,         // Color for buy signals (e.g., clrGreen)
   color sellColor,        // Color for sell signals (e.g., clrRed)
   bool enabled           // Enable colorizing
);

bool Colorizer_Destroy(int handle);

bool Colorizer_ColorCandle(
   int handle,
   datetime barTime,       // Bar to color
   int signalType         // SIGNAL_BUY, SIGNAL_SELL, SIGNAL_NONE
);

bool Colorizer_ColorCurrentCandle(int handle, int signalType);

void Colorizer_ClearAllSignals(int handle);  // Clear all colored candles

void Colorizer_Enable(int handle, bool enable);  // Enable/disable colorizing

bool Colorizer_IsEnabled(int handle);
bool Colorizer_IsIndicatorLoaded(int handle);

int    Colorizer_GetSignalsSet(int handle);  // Count of colored candles
string Colorizer_GetReport(int handle);
bool   Colorizer_IsInitialized(int handle);
```

**Usage Example**:
```cpp
int hColorizer = Colorizer_Create(_Symbol, PERIOD_CURRENT, hLogger,
                                  clrLime, clrRed, true);

// Color candle when signal is generated
int signal = GenerateSignal();

if(signal == SIGNAL_BUY)
{
   Colorizer_ColorCurrentCandle(hColorizer, SIGNAL_BUY);
}
else if(signal == SIGNAL_SELL)
{
   Colorizer_ColorCurrentCandle(hColorizer, SIGNAL_SELL);
}

// Color historical candle
datetime barTime = iTime(_Symbol, PERIOD_CURRENT, 5);
Colorizer_ColorCandle(hColorizer, barTime, SIGNAL_BUY);
```

---

### Module 20: License (TYPE_ID = 20)

**Purpose**: Validates EA license and authorized accounts.

**Functions**:
```cpp
int License_Create(int loggerHandle);

bool License_Destroy(int handle);

bool License_IsAuthorized(int handle);  // Check if current account is authorized

long License_GetAuthorizedLogin(int handle);  // Get authorized login number
long License_GetCurrentLogin(int handle);     // Get current login number

bool License_IsInitialized(int handle);
int  License_GetPoolUsage();
```

**Usage Example**:
```cpp
int OnInit()
{
   g_hLogger = Logger_Create("MyEA", LOG_LEVEL_INFO, LOG_OUTPUT_TERMINAL, true);

   // License check MUST be early in OnInit
   g_hLicense = License_Create(g_hLogger);
   if(g_hLicense < 0)
   {
      Logger_Error(g_hLogger, "Failed to create license module");
      return INIT_FAILED;
   }

   if(!License_IsAuthorized(g_hLicense))
   {
      long authorized = License_GetAuthorizedLogin(g_hLicense);
      long current = License_GetCurrentLogin(g_hLicense);

      Logger_Error(g_hLogger, StringFormat("License validation failed. Authorized: %I64d, Current: %I64d",
                                           authorized, current));
      Alert("This EA is not authorized for account: " + IntegerToString(current));
      return INIT_FAILED;
   }

   Logger_Info(g_hLogger, "License validated successfully");

   // Continue with other module initialization...
   return INIT_SUCCEEDED;
}
```

---

## Common Types and Enums (CommonTypes.mqh)

### Log Levels
```cpp
enum ENUM_LOG_LEVEL
{
   LOG_LEVEL_NONE    = 0,  // No logging
   LOG_LEVEL_ERROR   = 1,  // Errors only
   LOG_LEVEL_WARNING = 2,  // Warnings and errors
   LOG_LEVEL_INFO    = 3,  // Info, warnings, and errors
   LOG_LEVEL_DEBUG   = 4,  // Debug messages
   LOG_LEVEL_VERBOSE = 5   // All messages including verbose
};
```

### Log Output
```cpp
enum ENUM_LOG_OUTPUT
{
   LOG_OUTPUT_TERMINAL = 1,  // Terminal only
   LOG_OUTPUT_FILE     = 2,  // File only
   LOG_OUTPUT_BOTH     = 3   // Both terminal and file
};
```

### Execution Modes
```cpp
enum ENUM_EXECUTION_MODE
{
   EXECUTION_MODE_MARKET  = 0,  // Market execution
   EXECUTION_MODE_PENDING = 1   // Pending orders
};
```

### Signal Types
```cpp
enum ENUM_SIGNAL_TYPE
{
   SIGNAL_NONE      = 0,   // No signal
   SIGNAL_BUY       = 1,   // Buy signal
   SIGNAL_SELL      = 2,   // Sell signal
   SIGNAL_BUY_STOP  = 3,   // Buy stop pending
   SIGNAL_SELL_STOP = 4,   // Sell stop pending
   SIGNAL_BUY_LIMIT = 5,   // Buy limit pending
   SIGNAL_SELL_LIMIT = 6   // Sell limit pending
};
```

### Time Constants
```cpp
enum ENUM_HOUR
{
   HOUR_00 = 0, HOUR_01 = 1, HOUR_02 = 2, HOUR_03 = 3,
   HOUR_04 = 4, HOUR_05 = 5, HOUR_06 = 6, HOUR_07 = 7,
   HOUR_08 = 8, HOUR_09 = 9, HOUR_10 = 10, HOUR_11 = 11,
   HOUR_12 = 12, HOUR_13 = 13, HOUR_14 = 14, HOUR_15 = 15,
   HOUR_16 = 16, HOUR_17 = 17, HOUR_18 = 18, HOUR_19 = 19,
   HOUR_20 = 20, HOUR_21 = 21, HOUR_22 = 22, HOUR_23 = 23
};

enum ENUM_MINUTE
{
   MINUTE_00 = 0, MINUTE_05 = 5, MINUTE_10 = 10, MINUTE_15 = 15,
   MINUTE_20 = 20, MINUTE_25 = 25, MINUTE_30 = 30, MINUTE_35 = 35,
   MINUTE_40 = 40, MINUTE_45 = 45, MINUTE_50 = 50, MINUTE_55 = 55
};
```

### Slope and Trend States
```cpp
enum ENUM_SLOPE_THRESHOLD
{
   SLOPE_THRESHOLD_VERY_LOW  = 0,
   SLOPE_THRESHOLD_LOW       = 1,
   SLOPE_THRESHOLD_MODERATE  = 2,
   SLOPE_THRESHOLD_HIGH      = 3,
   SLOPE_THRESHOLD_VERY_HIGH = 4
};

enum ENUM_SLOPE_STATE
{
   SLOPE_STATE_FLAT     = 0,
   SLOPE_STATE_RISING   = 1,
   SLOPE_STATE_FALLING  = 2
};

enum ENUM_MA_TREND_STATE
{
   MA_TREND_UNDEFINED = 0,
   MA_TREND_UP        = 1,
   MA_TREND_DOWN      = 2,
   MA_TREND_SIDEWAYS  = 3
};
```

### Trading Direction
```cpp
enum ENUM_TRADING_DIRECTION
{
   TRADING_DIRECTION_BOTH = 0,  // Trade both directions
   TRADING_DIRECTION_LONG = 1,  // Long only
   TRADING_DIRECTION_SHORT = 2  // Short only
};
```

### Trigger Types
```cpp
enum ENUM_TRIGGER_TYPE
{
   TRIGGER_TIME_BASED        = 0,  // Time-based breakout
   TRIGGER_BREAKOUT          = 1,  // Price breakout
   TRIGGER_ZIGZAG_BREAKOUT   = 2,  // ZigZag level breakout
   TRIGGER_PATTERN           = 3,  // Pattern recognition
   TRIGGER_INDICATOR         = 4   // Indicator-based
};

enum ENUM_BREAKOUT_TYPE
{
   BREAKOUT_HIGH_LOW  = 0,  // High/Low breakout
   BREAKOUT_CLOSE     = 1,  // Close breakout
   BREAKOUT_BODY      = 2   // Body breakout
};
```

### Take Profit Types
```cpp
enum ENUM_TAKE_PROFIT_TYPE
{
   TP_FIXED       = 0,  // Fixed points
   TP_RISK_REWARD = 1,  // Risk-reward ratio
   TP_ZIGZAG      = 2,  // ZigZag levels
   TP_ATR         = 3   // ATR-based
};
```

### Stop Loss Types
```cpp
enum ENUM_STOP_LOSS_TYPE
{
   STOP_LOSS_ATR     = 0,  // ATR-based
   STOP_LOSS_FIXED   = 1,  // Fixed points
   STOP_LOSS_GRAPHIC = 2   // Graphic levels (swing high/low)
};
```

### Trailing Stop Types
```cpp
enum ENUM_TRAILING_STOP_TYPE
{
   TRAILING_STOP_NONE  = 0,  // No trailing
   TRAILING_STOP_FIXED = 1,  // Fixed step trailing
   TRAILING_STOP_ATR   = 2   // ATR-based trailing
};

enum ENUM_TRAILING_ACTIVATION
{
   TRAILING_ACTIVATION_IMMEDIATE = 0,  // Activate immediately
   TRAILING_ACTIVATION_RR        = 1,  // Activate at RR ratio
   TRAILING_ACTIVATION_PROFIT    = 2   // Activate at profit level
};

enum ENUM_PRICE_SOURCE
{
   PRICE_SOURCE_BID_ASK = 0,  // Use Bid/Ask prices
   PRICE_SOURCE_CLOSE   = 1   // Use close price
};
```

### Risk Types
```cpp
enum ENUM_RISK_TYPE
{
   RISK_FIXED_LOTS       = 0,  // Fixed lot size
   RISK_PERCENTAGE       = 1,  // Percentage of balance
   RISK_FIXED_ALLOCATION = 2   // Fixed capital allocation
};

enum ENUM_FORCE_CLOSE_MODE
{
   FORCE_CLOSE_NONE           = 0,  // No forced close
   FORCE_CLOSE_END_OF_DAY     = 1,  // Close at end of day
   FORCE_CLOSE_TIME_LIMIT     = 2,  // Close after time limit
   FORCE_CLOSE_PROFIT_TARGET  = 3   // Close at profit target
};
```

### Customer Profiles
```cpp
#define CUSTOMER_PROFILE_CONSERVATIVE 0
#define CUSTOMER_PROFILE_MODERATE     1
#define CUSTOMER_PROFILE_AGGRESSIVE   2
```

### Trend Detection
```cpp
enum ENUM_TREND_DIRECTION
{
   TREND_NEUTRAL = 0,
   TREND_UP      = 1,
   TREND_DOWN    = 2
};

enum ENUM_TREND_STRENGTH
{
   TREND_WEAK     = 0,
   TREND_MODERATE = 1,
   TREND_STRONG   = 2
};
```

### Book Analysis
```cpp
enum ENUM_PRESSURE_METHOD
{
   PRESSURE_SIMPLE      = 0,  // Simple volume sum
   PRESSURE_WEIGHTED    = 1,  // Weighted by level
   PRESSURE_EXPONENTIAL = 2   // Exponential decay
};

enum ENUM_WEIGHT_METHOD
{
   WEIGHT_UNIFORM     = 0,  // All levels equal weight
   WEIGHT_LINEAR      = 1,  // Linear decay with distance
   WEIGHT_EXPONENTIAL = 2   // Exponential decay
};

enum ENUM_BOOK_STATUS
{
   BOOK_STATUS_UNINITIALIZED = 0,
   BOOK_STATUS_READY         = 1,
   BOOK_STATUS_NO_DATA       = 2,
   BOOK_STATUS_ERROR         = 3
};
```

---

## EA Lifecycle and Flow

### OnInit Sequence

The initialization order is critical due to module dependencies:

```cpp
int OnInit()
{
   // 1. LOGGER (no dependencies)
   g_hLogger = Logger_Create("MyEA", LOG_LEVEL_INFO, LOG_OUTPUT_TERMINAL, true);
   if(g_hLogger < 0)
   {
      Print("ERROR: Failed to create Logger");
      return INIT_FAILED;
   }
   Logger_LogHeader(g_hLogger, "EA INITIALIZATION");

   // 2. LICENSE (requires Logger)
   g_hLicense = License_Create(g_hLogger);
   if(g_hLicense < 0 || !License_IsAuthorized(g_hLicense))
   {
      Logger_Error(g_hLogger, "License validation failed");
      return INIT_FAILED;
   }

   // 3. POSITION TRACKER (requires Logger)
   g_hPositionTracker = PositionTracker_Create(_Symbol, MAGIC_NUMBER, g_hLogger);
   if(g_hPositionTracker < 0) return INIT_FAILED;
   PositionTracker_RecoverStateAfterRestart(g_hPositionTracker);

   // 4. RISK MANAGER (requires Logger)
   g_hRiskManager = RiskManager_Create(_Symbol, MAGIC_NUMBER, g_hLogger,
                                       InpRiskType, InpFixedLots,
                                       InpInitialAllocation, InpRiskPercent,
                                       CUSTOMER_PROFILE_MODERATE);
   if(g_hRiskManager < 0) return INIT_FAILED;

   // Configure progression if enabled
   if(InpUseProgression)
   {
      RiskManager_SetProgression(g_hRiskManager, true, InpProgressionPercent,
                                InpMaxProgressionLevel, InpResetWins, InpResetLosses);
   }

   // 5. STOP LOSS MANAGER (requires Logger)
   g_hStopLoss = StopLoss_Create(_Symbol, PERIOD_CURRENT, g_hLogger,
                                 InpStopLossType, InpATRPeriod, InpATRMultiplier,
                                 InpFixedStopPoints, InpGraphicBuffer,
                                 InpMinStopPoints, InpMaxStopPoints);
   if(g_hStopLoss < 0) return INIT_FAILED;

   // 6. TAKE PROFIT MANAGER (requires Logger)
   g_hTakeProfit = TakeProfit_Create(_Symbol, PERIOD_CURRENT, g_hLogger,
                                     InpTakeProfitType, InpFixedTPPoints, InpRRRatio,
                                     0, 0, 0, 0, InpMinTPPoints, InpMaxTPPoints,
                                     0, 0.0, 0);
   if(g_hTakeProfit < 0) return INIT_FAILED;

   // 7. OCO SYSTEM (requires Logger)
   g_hOCO = OCO_Create(_Symbol, g_hLogger, MAGIC_NUMBER, 50, 200, true);
   if(g_hOCO < 0) return INIT_FAILED;

   // 8. TRAILING STOP (requires Logger + PositionTracker)
   if(InpUseTrailingStop)
   {
      g_hTrailingStop = TrailingStop_Create(_Symbol, PERIOD_CURRENT, g_hLogger, g_hPositionTracker,
                                           InpTrailingType, InpTrailingActivation,
                                           PRICE_SOURCE_BID_ASK, InpRRBreakeven, InpRRTrailing,
                                           InpTrailingStep, false, 2, 14, 1.0, 1.5, 10, 0.0);
      if(g_hTrailingStop < 0) return INIT_FAILED;
   }

   // 9. ORDER MANAGER (requires Logger + OCO)
   g_hOrderManager = OrderManager_Create(_Symbol, MAGIC_NUMBER, g_hLogger, g_hOCO, 0,
                                        InpMaxSlippage, InpUseOCO, InpRRRatio);
   if(g_hOrderManager < 0) return INIT_FAILED;

   // 10. POST EXECUTION MANAGER (requires Logger)
   if(InpUsePostExecution)
   {
      g_hPostExecution = PostExec_Create(_Symbol, PERIOD_CURRENT, g_hLogger,
                                        true, 2, 1);
      if(g_hPostExecution < 0) return INIT_FAILED;
   }

   // 11. TRIGGER SYSTEM (requires Logger)
   g_hTrigger = Trigger_Create(_Symbol, PERIOD_CURRENT, g_hLogger,
                               InpTriggerType, InpUseFirstBarOfDay,
                               InpRefCandleHour, InpRefCandleMin, InpRefCandleTolerance,
                               InpStartHour, InpStartMinute, InpWaitingTrigger,
                               InpBreakoutType, 0, 0, 0);
   if(g_hTrigger < 0) return INIT_FAILED;

   // 12. TREND DETECTOR (requires Logger)
   if(InpUseTrendFilter)
   {
      g_hTrendDetector = Trend_Create(_Symbol, PERIOD_CURRENT, g_hLogger,
                                     InpTrendMAPeriod, InpTrendMAMethod, 0, PRICE_CLOSE,
                                     0.9, 0.0001, 0.0003, 3, true);
      if(g_hTrendDetector < 0) return INIT_FAILED;
   }

   // 13. MULTI INDICATOR (requires Logger)
   if(InpUseIndicatorFilter)
   {
      g_hMultiIndicator = MultiInd_Create(_Symbol, PERIOD_CURRENT, g_hLogger,
                                         14, 3, 3, MODE_SMA, 0, 20.0, 80.0,
                                         14, PRICE_CLOSE, 30.0, 70.0,
                                         12, 5, 3);
      if(g_hMultiIndicator < 0) return INIT_FAILED;
   }

   // 14. BOOK ANALYSIS (requires Logger) - optional
   if(InpUseBookAnalysis)
   {
      g_hBook = Book_Create(_Symbol, 10, g_hLogger, false);
      if(g_hBook >= 0)
      {
         Book_Subscribe(g_hBook);
         Book_SetPressureConfig(g_hBook, PRESSURE_WEIGHTED, WEIGHT_LINEAR,
                               10, 0.8, 0.6, 0.6);
      }
   }

   // 15. CANDLE COLORIZER (requires Logger) - optional
   if(InpUseColorizer)
   {
      g_hColorizer = Colorizer_Create(_Symbol, PERIOD_CURRENT, g_hLogger,
                                     clrLime, clrRed, true);
   }

   Logger_Info(g_hLogger, "EA initialized successfully");
   return INIT_SUCCEEDED;
}
```

### OnTick Flow

```cpp
void OnTick()
{
   // 1. Check for new bar
   static datetime lastBarTime = 0;
   datetime currentBarTime = iTime(_Symbol, PERIOD_CURRENT, 0);
   bool isNewBar = (currentBarTime != lastBarTime);

   if(isNewBar)
   {
      lastBarTime = currentBarTime;
      OnNewBar();
   }

   // 2. Process trailing stops (MUST be called every tick)
   if(g_hTrailingStop >= 0)
   {
      TrailingStop_ProcessTrailingStops(g_hTrailingStop);
   }

   // 3. Monitor OCO pairs (MUST be called every tick)
   if(g_hOCO >= 0)
   {
      OCO_MonitorOCOPairs(g_hOCO);
   }

   // 4. Sync position tracker periodically
   static int tickCount = 0;
   if(++tickCount >= 100)
   {
      tickCount = 0;
      if(g_hPositionTracker >= 0)
      {
         PositionTracker_SyncWithMT5Positions(g_hPositionTracker);
      }
   }
}
```

### OnNewBar Flow (Signal Generation)

```cpp
void OnNewBar()
{
   // 1. Daily maintenance
   if(IsNewDay())
   {
      RiskManager_OnNewDay(g_hRiskManager);
      Trigger_Reset(g_hTrigger);
   }

   // 2. Check if can operate
   if(!RiskManager_CanOperate(g_hRiskManager))
   {
      Logger_Warning(g_hLogger, "Risk manager prevents trading");
      return;
   }

   // 3. Check trend filter (if enabled)
   if(g_hTrendDetector >= 0)
   {
      if(!Trend_Analyze(g_hTrendDetector))
         return;

      int trendDirection = Trend_GetDirection(g_hTrendDetector);
      if(trendDirection == TREND_NEUTRAL)
      {
         Logger_Debug(g_hLogger, "No clear trend - skipping");
         return;
      }
   }

   // 4. Generate signal
   Trigger_OnNewBar(g_hTrigger);
   int signal = Trigger_CheckTrigger(g_hTrigger);

   if(signal == SIGNAL_NONE)
      return;

   // 5. Filter signal with indicators (if enabled)
   if(g_hMultiIndicator >= 0)
   {
      MultiInd_RefreshData(g_hMultiIndicator);

      if(signal == SIGNAL_BUY)
      {
         if(!MultiInd_AreOversoldConditionsMet(g_hMultiIndicator, 1))
         {
            Logger_Debug(g_hLogger, "Buy signal rejected by indicator filter");
            return;
         }
      }
      else if(signal == SIGNAL_SELL)
      {
         if(!MultiInd_AreOverboughtConditionsMet(g_hMultiIndicator, 1))
         {
            Logger_Debug(g_hLogger, "Sell signal rejected by indicator filter");
            return;
         }
      }
   }

   // 6. Filter with book analysis (if enabled)
   if(g_hBook >= 0)
   {
      int bookSignal = Book_GetPressureSignal(g_hBook);
      if(bookSignal != SIGNAL_NONE && bookSignal != signal)
      {
         Logger_Debug(g_hLogger, "Signal rejected by order flow");
         return;
      }
   }

   // 7. Execute trade
   ExecuteTrade(signal);
}
```

### Trade Execution Pattern

```cpp
void ExecuteTrade(int signal)
{
   // 1. Get entry price
   double entryPrice = (signal == SIGNAL_BUY) ?
                       SymbolInfoDouble(_Symbol, SYMBOL_ASK) :
                       SymbolInfoDouble(_Symbol, SYMBOL_BID);

   // 2. Calculate stop loss
   datetime triggerBarTime = iTime(_Symbol, PERIOD_CURRENT, 1);
   double stopLoss = StopLoss_CalculateStopLoss(g_hStopLoss, signal, entryPrice, triggerBarTime);

   // 3. Calculate lot size
   double lotSize = RiskManager_CalculateLotSize(g_hRiskManager, entryPrice, stopLoss);

   // 4. Calculate take profit
   double takeProfit = TakeProfit_Calculate(g_hTakeProfit, signal, entryPrice, stopLoss);

   // 5. Notify risk manager
   RiskManager_OnNewOperation(g_hRiskManager);

   // 6. Execute order
   ulong ticket = OrderManager_ExecuteMarketOrder(g_hOrderManager, signal, lotSize,
                                                  entryPrice, stopLoss, takeProfit,
                                                  "Framework Trade");

   if(OrderManager_WasLastSuccessful(g_hOrderManager))
   {
      Logger_Info(g_hLogger, StringFormat("Position opened: #%I64u, Lot: %.2f", ticket, lotSize));

      // 7. Register position
      PositionTracker_RegisterPositionOpened(g_hPositionTracker, ticket, ticket);

      // 8. Activate trailing stop
      if(g_hTrailingStop >= 0)
      {
         TrailingStop_ActivateForPosition(g_hTrailingStop, ticket);
      }

      // 9. Color candle
      if(g_hColorizer >= 0)
      {
         Colorizer_ColorCurrentCandle(g_hColorizer, signal);
      }
   }
   else
   {
      Logger_Error(g_hLogger, "Order execution failed: " +
                  OrderManager_GetLastErrorDescription(g_hOrderManager));
   }
}
```

### OnTradeTransaction (Position Management)

```cpp
void OnTradeTransaction(const MqlTradeTransaction &trans,
                       const MqlTradeRequest &request,
                       const MqlTradeResult &result)
{
   // Handle position closures
   if(trans.type == TRADE_TRANSACTION_DEAL_ADD)
   {
      if(trans.deal_type == DEAL_TYPE_SELL || trans.deal_type == DEAL_TYPE_BUY)
      {
         // Check if this is a position close
         if(PositionSelectByTicket(trans.position))
         {
            // Position still exists - it's an entry
         }
         else
         {
            // Position closed
            HandlePositionClose(trans.position, trans.price, trans.volume);
         }
      }
   }
}

void HandlePositionClose(ulong positionId, double closePrice, double volume)
{
   // Calculate profit
   if(PositionSelectByTicket(positionId))
   {
      double profit = PositionGetDouble(POSITION_PROFIT);
      bool isWin = (profit > 0);

      // Notify risk manager
      RiskManager_OnOperationResult(g_hRiskManager, isWin, profit);

      // Unregister position
      PositionTracker_RegisterPositionClosed(g_hPositionTracker, positionId);

      // Deactivate trailing
      if(g_hTrailingStop >= 0)
      {
         TrailingStop_DeactivateForPosition(g_hTrailingStop, positionId);
      }

      Logger_Info(g_hLogger, StringFormat("Position closed: #%I64u, Profit: %.2f",
                                         positionId, profit));
   }
}
```

### OnDeinit (Cleanup)

CRITICAL: Destroy handles in REVERSE order of creation:

```cpp
void OnDeinit(const int reason)
{
   Logger_Info(g_hLogger, "EA deinitialization starting");

   // Destroy in REVERSE order
   if(g_hColorizer >= 0)
   {
      Colorizer_Destroy(g_hColorizer);
      g_hColorizer = -1;
   }

   if(g_hBook >= 0)
   {
      Book_Unsubscribe(g_hBook);
      Book_Destroy(g_hBook);
      g_hBook = -1;
   }

   if(g_hMultiIndicator >= 0)
   {
      MultiInd_Destroy(g_hMultiIndicator);
      g_hMultiIndicator = -1;
   }

   if(g_hTrendDetector >= 0)
   {
      Trend_Destroy(g_hTrendDetector);
      g_hTrendDetector = -1;
   }

   if(g_hTrigger >= 0)
   {
      Trigger_Destroy(g_hTrigger);
      g_hTrigger = -1;
   }

   if(g_hPostExecution >= 0)
   {
      PostExec_Destroy(g_hPostExecution);
      g_hPostExecution = -1;
   }

   if(g_hOrderManager >= 0)
   {
      OrderManager_Destroy(g_hOrderManager);
      g_hOrderManager = -1;
   }

   if(g_hTrailingStop >= 0)
   {
      TrailingStop_Destroy(g_hTrailingStop);
      g_hTrailingStop = -1;
   }

   if(g_hOCO >= 0)
   {
      OCO_Destroy(g_hOCO);
      g_hOCO = -1;
   }

   if(g_hTakeProfit >= 0)
   {
      TakeProfit_Destroy(g_hTakeProfit);
      g_hTakeProfit = -1;
   }

   if(g_hStopLoss >= 0)
   {
      StopLoss_Destroy(g_hStopLoss);
      g_hStopLoss = -1;
   }

   if(g_hRiskManager >= 0)
   {
      RiskManager_SaveStateToFile(g_hRiskManager);
      RiskManager_Destroy(g_hRiskManager);
      g_hRiskManager = -1;
   }

   if(g_hPositionTracker >= 0)
   {
      PositionTracker_Destroy(g_hPositionTracker);
      g_hPositionTracker = -1;
   }

   if(g_hLicense >= 0)
   {
      License_Destroy(g_hLicense);
      g_hLicense = -1;
   }

   if(g_hLogger >= 0)
   {
      Logger_Info(g_hLogger, "EA deinitialization complete");
      Logger_Destroy(g_hLogger);
      g_hLogger = -1;
   }
}
```

---

## Handle Creation Order Reference

Respecting module dependencies:

1. **Logger** - No dependencies
2. **License** - Requires: Logger
3. **PositionTracker** - Requires: Logger
4. **RiskManager** - Requires: Logger
5. **StopLossManager** - Requires: Logger
6. **TakeProfitManager** - Requires: Logger
7. **OCOSystem** - Requires: Logger
8. **TrailingStopManager** - Requires: Logger, PositionTracker
9. **OrderManager** - Requires: Logger, OCOSystem (optional)
10. **PostExecutionManager** - Requires: Logger
11. **TriggerSystem** - Requires: Logger
12. **TrendDetector** - Requires: Logger (internally uses MovingAverageSlope)
13. **MultiIndicatorAnalyzer** - Requires: Logger
14. **BookAnalysis** - Requires: Logger
15. **CandleColorizer** - Requires: Logger

---

## Common Strategy Patterns

### Pattern 1: Trend Following with Trigger

```cpp
// In OnNewBar()
if(Trend_Analyze(g_hTrendDetector))
{
   int trend = Trend_GetDirection(g_hTrendDetector);

   if(trend != TREND_NEUTRAL && Trend_IsConfirmed(g_hTrendDetector))
   {
      int signal = Trigger_CheckTrigger(g_hTrigger);

      // Only trade with the trend
      if((trend == TREND_UP && signal == SIGNAL_BUY) ||
         (trend == TREND_DOWN && signal == SIGNAL_SELL))
      {
         ExecuteTrade(signal);
      }
   }
}
```

### Pattern 2: Counter-Trend with Indicator Confirmation

```cpp
// In OnNewBar()
MultiInd_RefreshData(g_hMultiIndicator);

// Look for oversold/overbought extremes
if(MultiInd_AreOversoldConditionsMet(g_hMultiIndicator, 1))
{
   // Counter-trend buy at oversold
   ExecuteTrade(SIGNAL_BUY);
}
else if(MultiInd_AreOverboughtConditionsMet(g_hMultiIndicator, 1))
{
   // Counter-trend sell at overbought
   ExecuteTrade(SIGNAL_SELL);
}
```

### Pattern 3: Time-Based Breakout with Book Filter

```cpp
// In OnNewBar()
Trigger_OnNewBar(g_hTrigger);
int signal = Trigger_CheckTrigger(g_hTrigger);

if(signal != SIGNAL_NONE)
{
   // Confirm with order flow
   Book_ReadAndAnalyze(g_hBook);
   int bookSignal = Book_GetPressureSignal(g_hBook);
   double strength = Book_GetPressureStrength(g_hBook);

   if(bookSignal == signal && strength > 0.6)
   {
      ExecuteTrade(signal);
   }
}
```

### Pattern 4: Day Trade with Force Close

```cpp
input int InpCloseHour = 17;   // Force close hour
input int InpCloseMinute = 0;  // Force close minute

void OnTick()
{
   // Check for force close time
   MqlDateTime dt;
   TimeCurrent(dt);

   if(dt.hour == InpCloseHour && dt.min >= InpCloseMinute)
   {
      int openCount = PositionTracker_GetOpenCount(g_hPositionTracker);

      if(openCount > 0)
      {
         Logger_Info(g_hLogger, "Force closing all positions at end of day");
         OrderManager_CloseAllPositions(g_hOrderManager);
      }
   }

   // Normal tick processing...
}
```

### Pattern 5: Pending Orders with OCO

```cpp
void PlacePendingOCOOrders(int signalType)
{
   double currentPrice = (signalType == SIGNAL_BUY) ?
                         SymbolInfoDouble(_Symbol, SYMBOL_ASK) :
                         SymbolInfoDouble(_Symbol, SYMBOL_BID);

   // Calculate pending price (e.g., 20 points away)
   int pendingDistance = 20;
   double pendingPrice;

   if(signalType == SIGNAL_BUY)
      pendingPrice = currentPrice + pendingDistance * _Point;
   else
      pendingPrice = currentPrice - pendingDistance * _Point;

   // Calculate SL and TP
   double sl = StopLoss_CalculateStopLoss(g_hStopLoss, signalType, pendingPrice, TimeCurrent());
   double tp = TakeProfit_Calculate(g_hTakeProfit, signalType, pendingPrice, sl);

   // Calculate lot size
   double lotSize = RiskManager_CalculateLotSize(g_hRiskManager, pendingPrice, sl);

   // Place pending order
   ulong ticket = OrderManager_PlacePendingOrder(g_hOrderManager,
                                                 (signalType == SIGNAL_BUY) ? SIGNAL_BUY_STOP : SIGNAL_SELL_STOP,
                                                 lotSize, pendingPrice, pendingDistance, sl, tp, 0,
                                                 "Pending OCO");

   if(OrderManager_WasLastSuccessful(g_hOrderManager))
   {
      Logger_Info(g_hLogger, StringFormat("Pending order placed: #%I64u", ticket));
   }
}
```

---

## Important Rules and Best Practices

### MUST DO

1. **Always check handle >= 0** before using any module function
2. **Always destroy handles in REVERSE order** of creation in OnDeinit
3. **Always perform license check** in OnInit before other operations
4. **Always call RiskManager callbacks**:
   - `RiskManager_OnNewDay()` on new day
   - `RiskManager_OnNewOperation()` before opening position
   - `RiskManager_OnOperationResult()` after position closes
5. **Always call on every tick**:
   - `OCO_MonitorOCOPairs()` if using OCO
   - `TrailingStop_ProcessTrailingStops()` if using trailing stops
6. **Always validate lot sizes** and normalize to symbol specs
7. **Always check `RiskManager_CanOperate()`** before trading
8. **Always log errors** with meaningful messages

### NEVER DO

1. **Never use a handle without checking** if creation succeeded (handle >= 0)
2. **Never destroy modules in wrong order** (must be reverse of creation)
3. **Never skip license validation** in OnInit
4. **Never forget to call** `OCO_MonitorOCOPairs()` when using OCO
5. **Never modify OCO-managed positions** directly without notifying OCO system
6. **Never assume module state persists** after EA restart without recovery
7. **Never hardcode values** that should be in CommonTypes.mqh enums

### Error Handling Pattern

```cpp
int hModule = ModuleName_Create(...);
if(hModule < 0)
{
   Logger_Error(g_hLogger, "Failed to create ModuleName");
   // Clean up already-created modules
   return INIT_FAILED;
}

// Use module
bool result = ModuleName_SomeFunction(hModule, ...);
if(!result)
{
   Logger_Error(g_hLogger, "ModuleName operation failed: " + IntegerToString(GetLastError()));
   // Handle error appropriately
}
```

---

## Troubleshooting Guide

### Issue: "Cannot load library AlphaQuant_XXX.ex5"

**Cause**: Library file not in correct location

**Solution**:
- Verify .ex5 file exists in `MQL5/Libraries/` folder
- Check file name matches exactly (case-sensitive on some systems)
- Ensure library is not corrupted (re-download if necessary)
- Restart MetaEditor/MetaTrader

### Issue: Handle returns -1 on creation

**Cause**: Module initialization failed

**Solution**:
- Check logger for error messages (if Logger was created first)
- Verify all required parameters are valid
- Check if symbol/timeframe is valid
- Ensure dependencies were created first (e.g., Logger before others)
- Check pool capacity (use `ModuleName_GetPoolUsage()`)

### Issue: Compilation error "ModuleName_Function undeclared"

**Cause**: API header not included or not accessible

**Solution**:
- Verify `#include <Framework/FrameworkCore.mqh>` is present
- Check include path is correct
- Ensure API headers (.mqh files) are in correct location
- Verify no typos in function name
- Check if using correct module name prefix

### Issue: EA compiles but doesn't trade

**Cause**: Multiple possible causes

**Solution Checklist**:
1. Check license validation passed in OnInit
2. Verify `RiskManager_CanOperate()` returns true
3. Ensure signals are being generated (`Trigger_CheckTrigger()`)
4. Check log messages for filtering reasons
5. Verify trading hours/time filters
6. Check spread/market conditions
7. Ensure `OnTick()` and `OnNewBar()` are being called

### Issue: Trailing stop not working

**Cause**: Not calling ProcessTrailingStops or PositionTracker not synchronized

**Solution**:
- Ensure `TrailingStop_ProcessTrailingStops()` called every tick
- Verify position was activated with `TrailingStop_ActivateForPosition()`
- Check PositionTracker has position registered
- Verify activation conditions are met (RR ratio, profit level)
- Check log messages for trailing stop updates

### Issue: OCO orders not canceling

**Cause**: Not monitoring OCO pairs or position tracking issue

**Solution**:
- Ensure `OCO_MonitorOCOPairs()` called every tick
- Verify OCO pair was created successfully
- Check that position ticket is correct
- Call `OCO_OnPositionClose()` when position closes manually
- Check OCO debug info with `OCO_GetDebugInfo()`

### Issue: Risk manager prevents trading

**Cause**: Drawdown limit or other risk limit reached

**Solution**:
- Check `RiskManager_GetRiskReport()` for details
- Verify drawdown limits with `RiskManager_GetCurrentDrawdown()`
- Check progression state with `RiskManager_GetProgressionReport()`
- Review risk parameters in inputs
- Consider resetting with `RiskManager_Reset()` if appropriate

### Issue: Positions not recovered after restart

**Cause**: PositionTracker recovery not called or failed

**Solution**:
- Ensure `PositionTracker_RecoverStateAfterRestart()` called in OnInit
- Verify magic number matches positions
- Check symbol matches positions
- Call `PositionTracker_SyncWithMT5Positions()` to force sync
- Review logger messages for recovery details

---

## Advanced Topics

### Working with Multiple Symbols

```cpp
// Create separate module sets for each symbol
struct SymbolModules
{
   string symbol;
   int hPositionTracker;
   int hRiskManager;
   int hOrderManager;
   // ... other handles
};

SymbolModules g_modules[3]; // For 3 symbols

int OnInit()
{
   g_modules[0].symbol = "EURUSD";
   g_modules[1].symbol = "GBPUSD";
   g_modules[2].symbol = "USDJPY";

   for(int i = 0; i < 3; i++)
   {
      g_modules[i].hPositionTracker = PositionTracker_Create(g_modules[i].symbol, MAGIC_NUMBER, g_hLogger);
      // ... create other modules for each symbol
   }

   return INIT_SUCCEEDED;
}
```

### Custom Signal Combination

```cpp
int GenerateComplexSignal()
{
   // Combine multiple signal sources
   int trendSignal = GetTrendSignal();
   int triggerSignal = Trigger_CheckTrigger(g_hTrigger);
   int indicatorSignal = GetIndicatorSignal();
   int bookSignal = Book_GetPressureSignal(g_hBook);

   // Voting system: require 3 out of 4 agree
   int buyVotes = 0;
   int sellVotes = 0;

   if(trendSignal == SIGNAL_BUY) buyVotes++;
   else if(trendSignal == SIGNAL_SELL) sellVotes++;

   if(triggerSignal == SIGNAL_BUY) buyVotes++;
   else if(triggerSignal == SIGNAL_SELL) sellVotes++;

   if(indicatorSignal == SIGNAL_BUY) buyVotes++;
   else if(indicatorSignal == SIGNAL_SELL) sellVotes++;

   if(bookSignal == SIGNAL_BUY) buyVotes++;
   else if(bookSignal == SIGNAL_SELL) sellVotes++;

   if(buyVotes >= 3) return SIGNAL_BUY;
   if(sellVotes >= 3) return SIGNAL_SELL;

   return SIGNAL_NONE;
}
```

### Progressive Position Sizing

```cpp
void ExecuteTradeWithScaling(int signal)
{
   // Use RiskManager's progressive lot sizing
   double baseEntry = (signal == SIGNAL_BUY) ? SymbolInfoDouble(_Symbol, SYMBOL_ASK) : SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double baseSL = StopLoss_CalculateStopLoss(g_hStopLoss, signal, baseEntry, TimeCurrent());

   // First position with base risk
   double lot1 = RiskManager_CalculateLotSize(g_hRiskManager, baseEntry, baseSL);
   double tp1 = TakeProfit_Calculate(g_hTakeProfit, signal, baseEntry, baseSL);

   RiskManager_OnNewOperation(g_hRiskManager);
   ulong ticket1 = OrderManager_ExecuteMarketOrder(g_hOrderManager, signal, lot1, baseEntry, baseSL, tp1, "Entry 1");

   // Second position with 1.5R risk (if allowed)
   if(RiskManager_CanOperate(g_hRiskManager))
   {
      double lot2 = RiskManager_CalculateLotForR(g_hRiskManager, 1.5, baseEntry, baseSL);
      double tp2 = baseEntry + ((signal == SIGNAL_BUY ? 1 : -1) * 3.0 * MathAbs(baseEntry - baseSL));

      RiskManager_OnNewOperation(g_hRiskManager);
      ulong ticket2 = OrderManager_ExecuteMarketOrder(g_hOrderManager, signal, lot2, baseEntry, baseSL, tp2, "Entry 2");
   }
}
```

---

## Final Step: Cleanup Unused Inputs

### Why Clean Up?

After implementing your custom strategy, the Template will contain many input parameters for modules you're not using. To make the EA easier for end-users to configure:

**ALWAYS comment out unused input groups** before delivery.

### How to Identify Unused Modules

Check which module handles are never created in OnInit():

```cpp
// Example: MicroCanal EA uses:
✅ g_loggerHandle      (Logger_Create called)
✅ g_licenseHandle     (License_Create called)
✅ g_posTrackerHandle  (PositionTracker_Create called)
✅ g_riskHandle        (RiskManager_Create called)
✅ g_slHandle          (StopLoss_Create called)
✅ g_tpHandle          (TakeProfit_Create called)
✅ g_orderHandle       (OrderManager_Create called)
✅ g_trendHandle       (Trend_Create called)

❌ g_triggerHandle     (NOT created - never used)
❌ g_multiIndHandle    (NOT created - never used)
❌ g_bookHandle        (NOT created - never used)
❌ g_postExecHandle    (NOT created - never used)
```

### Cleanup Process

**Step 1**: Comment out unused input groups:

```cpp
// Original (verbose):
input group "=== [12] TRIGGER SYSTEM ==="
input bool  inp_UseTrigger = false;
input int   inp_TriggerRefHour = 10;
// ... 10+ more trigger inputs

// After cleanup (commented):
/*
//+------------------------------------------------------------------+
//| [12] TRIGGER SYSTEM (NOT USED IN THIS STRATEGY)                 |
//+------------------------------------------------------------------+
input group "=== [12] TRIGGER SYSTEM ==="
input bool  inp_UseTrigger = false;
input int   inp_TriggerRefHour = 10;
// ... 10+ more trigger inputs
*/
```

**Step 2**: Add a comment header explaining what was removed:

```cpp
//+------------------------------------------------------------------+
//| UNUSED MODULES (commented out for clarity)                      |
//| To re-enable: uncomment the desired group and create handle     |
//+------------------------------------------------------------------+
//
// The following input groups are commented because this strategy
// does not use these modules:
//   - [12] TRIGGER SYSTEM
//   - [14] MULTI INDICATOR ANALYZER
//   - [15] BOOK ANALYSIS
//
// To re-enable any module:
// 1. Uncomment the input group
// 2. Create the module handle in OnInit()
// 3. Destroy the handle in OnDeinit()
```

### Example: MicroCanal EA Cleanup

For the MicroCanal breakout strategy, comment out:

```cpp
✅ Keep Active:
  [1] CONFIGURACOES GERAIS
  [2] LOGGER
  [3] HORARIOS DE TRADING
  [4] CONTROLE DE OPERACOES
  [5] EXECUTION / ORDER MANAGER
  [6] GESTAO DE RISCO
  [7] STOP LOSS
  [8] TAKE PROFIT
  [9] TRAILING STOP (optional - user configurable)
  [13] MEDIA MOVEL / TREND DETECTOR (if using trend filter)
  [17] ESTRATEGIA MICRO CANAL (custom inputs)

❌ Comment Out:
  [10] OCO SYSTEM (if not using OCO)
  [11] POST EXECUTION (if not using post-execution)
  [12] TRIGGER SYSTEM (not used by MicroCanal)
  [14] MULTI INDICATOR ANALYZER (not used)
  [15] BOOK ANALYSIS (not used)
  [16] VISUALIZATION (optional)
```

### Benefits of Cleanup

- ✅ **Simpler UI**: End-user sees only relevant parameters
- ✅ **Faster Configuration**: Less scrolling, less confusion
- ✅ **Clear Intent**: Strategy purpose is obvious from inputs
- ✅ **Preserved Code**: Commented code remains for future reference
- ✅ **Easy Reactivation**: Just uncomment + create handle if needed later

### Automated Cleanup Checklist

When finishing an EA, verify:

1. ✅ All unused input groups are commented out
2. ✅ Comment header explains what was removed and how to re-enable
3. ✅ Only modules actually created in OnInit have active inputs
4. ✅ Test compilation after cleanup (should still compile cleanly)
5. ✅ Test parameter window in MT5 (verify clean UI)

---

## Summary Checklist for Coding Assistants

When helping a client build an EA with the alphaQuant Framework:

**Preparation**:
- [ ] Confirm they have .ex5 libraries in MQL5/Libraries/
- [ ] Confirm they have API headers accessible
- [ ] **CRITICAL**: Copy ModularEA_Template.mq5 to new file (e.g., StrategyName_EA.mq5)
- [ ] **NEVER modify the original template**

**Development**:
- [ ] Include FrameworkCore.mqh
- [ ] Define input parameters based on strategy
- [ ] Declare global handles (initialized to -1)
- [ ] Create modules in OnInit in dependency order
- [ ] Always check handles >= 0 after creation
- [ ] Implement license validation before other operations
- [ ] Implement OnTick with new bar detection
- [ ] Call OCO_MonitorOCOPairs and TrailingStop_ProcessTrailingStops every tick
- [ ] Implement signal generation logic
- [ ] Implement trade execution with proper SL/TP calculation
- [ ] Call RiskManager callbacks appropriately
- [ ] Implement OnDeinit with reverse-order cleanup
- [ ] Add comprehensive logging throughout

**Cleanup (CRITICAL)**:
- [ ] **Comment out all unused input groups** (see "Final Step: Cleanup Unused Inputs")
- [ ] Add comment header explaining what was removed
- [ ] Verify only active modules have visible inputs
- [ ] Test compilation after cleanup

**Testing**:
- [ ] Test compilation in MetaEditor (should be 0 errors, 0 warnings)
- [ ] Verify parameter window shows only relevant inputs
- [ ] Provide testing guidance for Strategy Tester
- [ ] Document strategy-specific configuration

---

**End of Guide**

This guide should be used as a comprehensive reference when building new EAs with the alphaQuant Framework. Always refer to the specific module sections for complete function signatures and usage examples.
