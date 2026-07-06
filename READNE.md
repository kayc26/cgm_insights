 ## Goal / Value Prop
For health-conscious people who wear CGM and would like to have more stable glucose levels, CGM insight is a digital advisor that trained on individual diet and glucose data and offer personalized recommendations to stablize post-meal glucose level.


 ## Data
 1. Glucose Data: two weeks of raw glucose data collected with Lingo 
 2. Diet Data: manual food journal in Bevel + carb labeling (rice/bread/potato... for GI claculation)
 3. Movement Data: step counts from apple watch
 4. Both data exported from Apple Health

 ## Preprocessing
 1. Limit data from selected time frame and sources
 2. drop duplicates
 3. meal data curation: keep calories, protein, carbs, fat, fiber, GI 
 4. aggregate food items consumed within 15 minutes as one meal
 5. align glucose data with meals (response window = 2hr), get baseline_window, peak rise, iauc, 
 6. motion data: define walked_after_eating if post_steps > 200

 ## Model
 1. Train-Test Split: 
    - train: window 1 (14 days)
    - test: window 2 (14 days)

 2. target: peak_rise / iauc
 3. model: linear regression
 4. evaluation: r2 accuracy? 

 ## Recommendation Model
 1. stratefies: 
 - swap to a lower-GI carb source; GI * 0.5
 - add a side of low-carb vegetables: fiber += 3
 - take a walk: walked after steps + 200
 2. calculate predicted iauc / peak_rise with each strategy
 3. recommend the strategy with most significant iauc/peak_rise reduction

 ## Limitations
 1. limited training data
 2. potential inaccurate food nutrition values
 3. motion data limited to step counts only (possibly related to HRV, hear rate etc.)
