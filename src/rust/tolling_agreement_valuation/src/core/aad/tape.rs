use std::cell::RefCell;

// Global thread-local tape
thread_local! {
    pub static TAPE: RefCell<Tape> = RefCell::new(Tape::new());
}

pub struct Tape {
    pub nodes: Vec<Node>,
}

impl Tape {
    pub fn new() -> Self {
        Tape { nodes: Vec::with_capacity(10000) }
    }
    
    pub fn push(&mut self, node: Node) -> usize {
        let idx = self.nodes.len();
        self.nodes.push(node);
        idx
    }
    
    pub fn clear(&mut self) {
        self.nodes.clear();
    }

    /// Propagates derivatives backwards from the output.
    /// `adjoints` must be a vector of size `nodes.len()`, initialized with zeros,
    /// except for the target output node(s) which should be 1.0.
    pub fn execute_backward(&self, adjoints: &mut [f64]) {
        if adjoints.len() != self.nodes.len() {
            panic!("Adjoints vector length {} does not match tape length {}", adjoints.len(), self.nodes.len());
        }

        // Iterate backwards from the last node
        for i in (0..self.nodes.len()).rev() {
            let node = &self.nodes[i];
            let adj_i = adjoints[i];
            
            // Optimization: If adjoint is zero, no need to propagate
            if adj_i == 0.0 {
                continue;
            }

            for (parent_idx, weight) in node.parents.iter().zip(node.weights.iter()) {
                adjoints[*parent_idx] += adj_i * weight;
            }
        }
    }
}

pub struct Node {
    // The partial derivatives dw/d_parent
    pub weights: Vec<f64>,
    // Indices of parent nodes (in the graph) in the nodes vector 
    pub parents: Vec<usize>,
}

// Helper function to push a node to the thread-local tape
pub fn push_to_tape(weights: Vec<f64>, parents: Vec<usize>) -> usize {
    TAPE.with(|tape_cell| {
        let mut tape = tape_cell.borrow_mut();
        tape.push(Node { weights, parents })
    })
}

// Helper to clear the thread-local tape
pub fn clear_tape() {
    TAPE.with(|tape_cell| {
        tape_cell.borrow_mut().clear();
    })
}

// Helper to get tape length (for sizing adjoint vector)
pub fn get_tape_len() -> usize {
    TAPE.with(|tape_cell| {
        tape_cell.borrow().nodes.len()
    })
}

// Helper to execute backward pass on the thread-local tape
pub fn backward(adjoints: &mut [f64]) {
    TAPE.with(|tape_cell| {
        tape_cell.borrow().execute_backward(adjoints);
    })
}
