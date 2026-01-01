use clap::{Args, Parser, Subcommand};

#[derive(Parser)]
#[command(author, version, about)]
pub struct Cli {
    #[command(subcommand)]
    pub command: Commands,
}

#[derive(Subcommand)]
pub enum Commands {
    /// Calculate the profit (valuation)
    CalculateProfit(CalculateProfitArgs),
    // Sample price paths
    SamplePrices(SamplePathsArgs),
}

#[derive(Args, Debug)]
pub struct SamplePathsArgs {
    #[arg(
        long,
        default_value = "/Users/simonperschel/Documents/coding/python/tolling-agreement/data/forward-curve/gas-forward-hourly.csv"
    )]
    pub gas_curve: String,
    #[arg(
        long,
        default_value = "/Users/simonperschel/Documents/coding/python/tolling-agreement/data/forward-curve/power-forward-hourly.csv"
    )]
    pub power_curve: String,
    #[arg(
        long,
        default_value = "/Users/simonperschel/Documents/coding/python/tolling-agreement/data/parameters/parameters.json"
    )]
    pub model_params: String,
    #[arg(short, long, default_value_t = 1000)]
    pub num_paths: usize,
}

#[derive(Args, Debug)]
pub struct CalculateProfitArgs {
    #[arg(
        long,
        default_value = "/Users/simonperschel/Documents/coding/python/tolling-agreement/data/forward-curve/gas-forward-hourly.csv"
    )]
    pub gas_curve: String,
    #[arg(
        long,
        default_value = "/Users/simonperschel/Documents/coding/python/tolling-agreement/data/forward-curve/power-forward-hourly.csv"
    )]
    pub power_curve: String,
    #[arg(
        long,
        default_value = "/Users/simonperschel/Documents/coding/python/tolling-agreement/data/parameters/parameters.json"
    )]
    pub model_params: String,
    #[arg(
        long,
        default_value = "/Users/simonperschel/Documents/coding/python/tolling-agreement/data/facility/parameters.json"
    )]
    pub unit_params: String,
    #[arg(short, long, default_value_t = 1000)]
    pub num_paths: usize,
}
