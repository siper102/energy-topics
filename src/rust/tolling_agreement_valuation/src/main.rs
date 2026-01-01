mod cli;
mod commands;
mod data;
mod data_reader;
mod engine;
mod processes;
use crate::cli::{Cli, Commands};
use anyhow::Result;
use clap::Parser;

fn main() -> Result<()> {
    let args = Cli::parse();

    match args.command {
        Commands::CalculateProfit(cmd_args) => {
            let profit = commands::calculate_profit::CalculateProfitCommand::execute(cmd_args)?;
            println!("--------------------------------");
            println!("✅ Valuation Complete");
            println!("💰 NPV: {:.2} EUR", profit);
            println!("--------------------------------");
        }
        Commands::SamplePrices(cmd_args) => {
            commands::sample_prices::SamplePricesCommand::execute(cmd_args)?;
        }
    }

    Ok(())
}
