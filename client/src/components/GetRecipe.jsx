import { useEffect, useState } from "react";
import RecipeCarousel from "./RecipeCarousel";
import SimpleHeader from "./Header";
import { useIngredients } from "../context/RecipesContext";

export default function Recipe() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [recipes, setRecipes] = useState([]);
  const { selectedIngredient } = useIngredients();
  const apiHost = import.meta.env.VITE_API_HOST;



  useEffect(() => {

    const getRecipe = async () => {
      try {
        setLoading(true);
        const ingredients = selectedIngredient
          .map((name) => name.trim().toLowerCase().split(" ").join("+"))
          .join(",+");

        const response = await fetch(
          `${apiHost}/api/recipes?ingredients=${ingredients}`
        );
        if (!response.ok) {
          throw new Error(`${response.status}`);
        }

        const data = await response.json();
        setRecipes(data);
      } catch (error) {
        console.error("Error occurred while loading recipes.", error);
        setError(error);
      } finally {
        setLoading(false);
      }
    };
    getRecipe();
  }, [selectedIngredient]);

  return (
    <div className="page-content">
      <SimpleHeader />
      <div className="carousel-wrapper">
        <h1>Your WasteNot Menu</h1>
        {loading && <p>Loading...</p>}
        {error && <p>Oops! We couldn't load recipes. Try selecting a few ingredients first.</p>}
        {!loading && !error && <RecipeCarousel recipes={recipes} />}
      </div>
    </div>
  );
}
