#![cfg_attr(not(feature = "std"), no_std)]

use ink_lang as ink;

/// SavedMacros ink! 3.x contract — compatible with Portaldot (Substrate 2.x)
///
/// Allows users to save frequently-used AI commands (macros) on-chain.
#[ink::contract]
mod saved_macros {
    use ink_prelude::string::String;
    use ink_prelude::vec::Vec;
    use ink_storage::traits::{PackedLayout, SpreadLayout};
    use ink_storage::Mapping;

    const MAX_MACROS: u32 = 10;

    #[derive(
        scale::Decode,
        scale::Encode,
        Clone,
        SpreadLayout,
        PackedLayout,
    )]
    #[cfg_attr(
        feature = "std",
        derive(scale_info::TypeInfo, ink_storage::traits::StorageLayout)
    )]
    pub struct Macro {
        pub name:       String,
        pub intent:     String,
        pub params:     String,
        pub updated_at: u32,
    }

    #[ink(storage)]
    pub struct SavedMacros {
        macros:      Mapping<AccountId, Vec<Macro>>,
        total_saves: u64,
    }

    #[ink(event)]
    pub struct MacroSaved {
        #[ink(topic)]
        account: AccountId,
        name:    String,
    }

    #[derive(scale::Decode, scale::Encode, Debug, PartialEq)]
    #[cfg_attr(feature = "std", derive(scale_info::TypeInfo))]
    pub enum Error {
        TooManyMacros,
        NameTooLong,
        ParamsTooLong,
        MacroNotFound,
        EmptyName,
    }

    pub type Result<T> = core::result::Result<T, Error>;

    impl SavedMacros {
        #[ink(constructor)]
        pub fn new() -> Self {
            Self {
                macros:      Mapping::default(),
                total_saves: 0,
            }
        }

        /// Save or update a macro for the caller.
        #[ink(message)]
        pub fn save_macro(
            &mut self,
            name:   String,
            intent: String,
            params: String,
        ) -> Result<()> {
            if name.is_empty() {
                return Err(Error::EmptyName);
            }
            if name.len() > 64 {
                return Err(Error::NameTooLong);
            }
            if params.len() > 512 {
                return Err(Error::ParamsTooLong);
            }

            let caller = self.env().caller();
            let block  = self.env().block_number();
            let mut list = self.macros.get(&caller).unwrap_or_default();

            if let Some(m) = list.iter_mut().find(|m| m.name == name) {
                m.intent     = intent;
                m.params     = params;
                m.updated_at = block;
            } else {
                if list.len() as u32 >= MAX_MACROS {
                    return Err(Error::TooManyMacros);
                }
                list.push(Macro { name: name.clone(), intent, params, updated_at: block });
            }

            self.macros.insert(&caller, &list);
            self.total_saves = self.total_saves.saturating_add(1);
            self.env().emit_event(MacroSaved { account: caller, name });
            Ok(())
        }

        /// Delete a macro by name.
        #[ink(message)]
        pub fn delete_macro(&mut self, name: String) -> Result<()> {
            let caller = self.env().caller();
            let mut list = self.macros.get(&caller).unwrap_or_default();
            let before = list.len();
            list.retain(|m| m.name != name);
            if list.len() == before {
                return Err(Error::MacroNotFound);
            }
            self.macros.insert(&caller, &list);
            Ok(())
        }

        /// Get all macros for the caller.
        #[ink(message)]
        pub fn get_macros(&self) -> Vec<Macro> {
            self.macros.get(&self.env().caller()).unwrap_or_default()
        }

        /// Total saves across all users.
        #[ink(message)]
        pub fn total_saves(&self) -> u64 {
            self.total_saves
        }
    }
}
