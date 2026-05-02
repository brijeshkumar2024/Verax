export type Category = "restaurant" | "gym" | "salon" | "dentist" | "pharmacy";

export type TriggerType =
  | "spike"
  | "drop"
  | "high_cart_abandon"
  | "low_repeat_rate"
  | "new_competitor"
  | "rating_dip"
  | "inventory_expiry"
  | "weekend_opportunity";

export type ComposePayload = {
  category: Category;
  merchant: {
    merchant_id: string;
    name: string;
    category: Category;
    city: string;
    avg_order_value: number;
    weekly_orders: number;
    conversion_rate: number;
    repeat_customer_rate: number;
    rating: number;
    margin_pct: number;
  };
  trigger: {
    type: TriggerType;
    observed_value: number;
    baseline_value: number;
    window_minutes: number;
    timestamp_utc: string;
  };
  customer?: {
    customer_id: string;
    loyalty_tier: "new" | "silver" | "gold" | "platinum";
    visits_last_30d: number;
    spend_last_30d: number;
    last_engagement_days: number;
  };
};

export type ComposeResponse = {
  message: string;
  cta: string;
  send_as: "vera" | "system" | "merchant";
  suppression_key: string;
  suppressed: boolean;
  rationale: string[];
  decision_score: number;
  score_components?: {
    decision_quality: number;
    specificity: number;
    category_fit: number;
    merchant_fit: number;
    engagement: number;
  };
  rule_trace?: string;
};
